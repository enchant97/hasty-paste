import logging
import secrets
import string
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from aiofiles import open as aio_open
from aiofiles import os as aio_os
from aiofiles import ospath as aio_ospath
from pydantic import BaseModel, ValidationError, validator
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (find_lexer_class_by_name, get_all_lexers,
                             get_lexer_by_name)
from pygments.util import ClassNotFound as PygmentsClassNotFound
from quart import Response, abort, make_response
from quart.utils import run_sync
from quart.wrappers import Body
from werkzeug.wrappers import Response as WerkzeugResponse

from .config import ExpireTimeDefaultSettings

logger = logging.getLogger("paste_bin")

PASTE_ID_CHARACTER_SET = string.ascii_letters + string.digits
CURRENT_PASTE_META_VERSION = 1


class PasteException(Exception):
    pass


class PasteMetaException(Exception):
    pass


class PasteIdException(PasteException):
    pass


class PasteDoesNotExistException(PasteException):
    pass


class PasteExpiredException(PasteException):
    pass


class PasteMetaUnprocessable(PasteMetaException):
    pass


class PasteMetaVersionInvalid(PasteMetaException):
    pass


class PasteMetaVersion(BaseModel):
    version: int = CURRENT_PASTE_META_VERSION


class PasteMeta(PasteMetaVersion):
    paste_id: str
    creation_dt: datetime
    expire_dt: datetime | None = None
    lexer_name: str | None = None
    title: str | None = None

    @property
    def is_expired(self) -> bool:
        if self.expire_dt is not None and self.expire_dt.replace(tzinfo=None) < datetime.utcnow():
            return True
        return False

    def raise_if_expired(self):
        if self.is_expired:
            raise PasteExpiredException(f"paste has expired with id of {paste_id}")


class PasteMetaCreate(BaseModel):
    content: str
    long_id: bool = False
    expire_dt: datetime | None = None
    lexer_name: str | None = None
    title: str | None = None

    @validator("title")
    def validate_title(cls, title: str | None):
        if title is not None and len(title) > 32:
            raise ValueError("title must be < 32")
        return title

    @validator("lexer_name")
    def validate_lexer_name(cls, lexer_name: str | None):
        if lexer_name is not None and not is_valid_lexer_name(lexer_name):
            raise ValueError("not valid lexer name")
        return lexer_name


def get_paste_meta(meta_line: str | bytes) -> PasteMeta:
    """
    Processes a meta line and converts it into a object.

        :param meta_line: The meta line to process
        :raises PasteMetaVersionInvalid: Raised when the meta version is detected to be unsupported
        :raises PasteMetaUnprocessable: Raised when the meta is not valid
        :return: The valid meta object
    """
    try:
        version = PasteMetaVersion.parse_raw(meta_line).version
        # NOTE this allows for future support if the meta format was to change
        if version != CURRENT_PASTE_META_VERSION:
            logger.error("failed to load paste meta, version not supported: '%s'", meta_line)
            raise PasteMetaVersionInvalid(f"paste is not a valid version number of '{version}'")
        return PasteMeta.parse_raw(meta_line)
    except ValidationError as err:
        logger.error("failed to load paste meta, validation did not pass: '%s'", meta_line)
        raise PasteMetaUnprocessable("paste meta cannot be loaded") from err


def gen_id(n: int) -> str:
    """
    Generate a secure id from `PASTE_ID_CHARACTER_SET`

        :param n: How many characters to generate
        :return: the generated id
    """
    return "".join(secrets.choice(PASTE_ID_CHARACTER_SET) for _ in range(n))


def create_paste_id(long: bool = False) -> str:
    """
    Creates a paste id, if in 'long' mode will
    generate a very long id meant to
    reduce chance of a brute force attack

        :param long: Whether to use the long id, defaults to False
        :return: The generated id
    """
    if long:
        return gen_id(40)
    return gen_id(10)


def create_paste_path(root_path: Path, paste_id: str, mkdir: bool = False) -> Path:
    """
    Combines a the paste root with a paste's id to form the full path.
    Will also optionally ensure the directories are created

        :param root_path: The root path to use as a base
        :param paste_id: The paste's id
        :param mkdir: Creates the directories if not found, defaults to False
        :raises PasteIdException: If the given id was invalid
        :return: The combined path
    """
    if len(paste_id) < 3:
        raise PasteIdException("paste_id too short, must be at least 3 characters long")
    full_path = root_path / paste_id[:2]
    if mkdir:
        full_path.mkdir(parents=True, exist_ok=True)
    return full_path / paste_id[2:]


def get_id_from_paste_path(root_path: Path, paste_path: Path) -> str:
    """
    Deconstruct a paste path, returing the full paste id

        :param root_path: The root pastes path
        :param paste_path: The paste file location
        :return: The paste id
    """
    return "".join(paste_path.relative_to(root_path).parts)


def get_all_paste_id_parts(root_path: Path) -> Generator[str, None, None]:
    """
    Yields each paste id part found

        :param root_path: The root pastes path
        :yield: A pastes id part
    """
    for part in root_path.glob("*"):
        yield part.name


def get_all_paste_ids_from_part(root_path: Path, id_part: str) -> Generator[str, None, None]:
    """
    Yield each paste id from a id part directory

        :param root_path: The root pastes path
        :param id_part: The id part
        :yield: The full paste id
    """
    for part in root_path.joinpath(id_part).glob("*"):
        yield id_part + part.name


def get_all_paste_ids(root_path: Path) -> Generator[str, None, None]:
    for id_part in get_all_paste_id_parts(root_path):
        for full_id in get_all_paste_ids_from_part(root_path, id_part):
            yield full_id


def get_paste_ids_as_csv(root_path: Path) -> Generator[str, None, None]:
    for paste_id in get_all_paste_ids(root_path):
            yield paste_id + "\n"


async def write_paste(
        paste_path: Path,
        paste_meta: PasteMeta,
        content: AsyncGenerator[bytes, None] | Body | bytes):
    """
    Writes a new paste

        :param paste_path: The full paste path
        :param paste_meta: The pastes meta
        :param content: The paste content
    """
    async with aio_open(paste_path, "wb") as fo:
        await fo.write(paste_meta.json().encode() + b"\n")
        if isinstance(content, (AsyncGenerator, Body)):
            async for chunk in content:
                await fo.write(chunk)
        else:
            await fo.write(content)


async def read_paste_meta(paste_path: Path) -> PasteMeta:
    """
    Read just the paste's meta from file

        :param paste_path: The full paste path
        :return: The meta
    """
    async with aio_open(paste_path, "rb") as fo:
        meta = get_paste_meta(await fo.readline())
        return meta


async def read_paste_content(paste_path: Path) -> AsyncGenerator[bytes, None]:
    """
    Read just the paste's content from file

        :param paste_path: The full paste path
        :yield: The paste content as bytes
    """
    async with aio_open(paste_path, "rb") as fo:
        # TODO use tell+seek+read to save memory while checking for newline
        _ = await fo.readline()
        async for line in fo:
            yield line


def get_form_datetime(value: str | None) -> datetime | None:
    """
    Handle loading a datetime from form input

        :param value: The form value
        :return: The processed datetime or None
    """
    if value:
        return datetime.fromisoformat(value)


async def safe_remove_paste(paste_path: Path, paste_id: str):
    """
    deletes a paste from disk,
    skipping if it no longer exists

        :param paste_path: The full path to paste
        :param paste_id: The paste's id
    """
    logger.info("auto removing of paste with id of '%s'", paste_id)
    try:
        await aio_os.remove(paste_path)
    except FileNotFoundError:
        pass


async def try_get_paste(
        root_path: Path,  # TODO make this path_path
        paste_id: str,
        **kw  # TODO remove
        ) -> tuple[Path, PasteMeta]:
    """
    Try to process the paste meta

        :param root_path: The root path
        :param paste_id: The paste's id
        :raises PasteDoesNotExistException: When the paste is not found
        :raises PasteExpiredException: When the paste has expired
        :return: The paste's full path and it's loaded meta
    """
    paste_path = create_paste_path(root_path, paste_id)

    if not await aio_ospath.isfile(paste_path):
        logger.info("paste id of '%s' not found on filesystem", paste_id)
        raise PasteDoesNotExistException(f"paste not found with id of {paste_id}")

    paste_meta = await read_paste_meta(paste_path)

    paste_meta.raise_if_expired()

    return paste_path, paste_meta


# FIXME remove
async def try_get_paste_with_content_response(
        root_path: Path,
        paste_id: str,
        ) -> tuple[Path, PasteMeta, Response | WerkzeugResponse]:
    """
    An extension of `try_get_paste()`,
    will also return the paste contents in a response

        :param root_path: The root path
        :param paste_id: The paste's id
        :return: The paste's full path, it's meta and the content response
    """
    paste_path, paste_meta = await try_get_paste(root_path, paste_id)

    response = await make_response(read_paste_content(paste_path))
    response.mimetype = "text/plain"

    return paste_path, paste_meta, response


async def list_paste_ids_response(root_path: Path) -> Response | WerkzeugResponse:
    response = await make_response(get_paste_ids_as_csv(root_path))
    response.mimetype = "text/csv"

    return response


def handle_paste_exceptions(func):
    """
    Used as a decorator, to handle
    `PasteException` and `PasteMetaException` errors
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PasteException as err:
            logger.debug(
                "catching PasteException in request and aborting with 404",
                exc_info=err
            )
            abort(404)
        except PasteMetaException as err:
            logger.debug(
                "catching PasteMetaException in request and aborting with 500",
                exc_info=err
            )
            abort(500)
    return wrapper


def get_highlighter_names() -> Generator[str, None, None]:
    """
    Return all highlighter names

        :yield: Each highlighter name
    """
    for lexer in get_all_lexers():
        if lexer[1]:
            yield lexer[1][0]


def is_valid_lexer_name(lexer_name: str) -> bool:
    """
    Check whether the given name is a valid lexer name

        :param lexer_name: The name to check
        :return: Whether it is valid
    """
    try:
        _ = find_lexer_class_by_name(lexer_name)
        return True
    except PygmentsClassNotFound:
        return False


def highlight_content(content: str, lexer_name: str) -> str:
    """
    Highlight some content with a given lexer,
    will fallback to default lexer if given one is not found

        :param content: The content to highlight
        :param lexer_name: The lexer to use
        :return: The highlighted content as html
    """
    lexer = get_lexer_by_name("text", stripall=True)

    if lexer_name:
        try:
            lexer = get_lexer_by_name(lexer_name, stripall=True)
        except PygmentsClassNotFound:
            logger.debug("skipping code highlighting as no lexer was found by '%s'", lexer_name)

    formatter = HtmlFormatter(linenos="inline", cssclass="highlighted-code")

    return highlight(content, lexer, formatter)


@run_sync
def highlight_content_async_wrapped(content: str, lexer_name: str) -> str:
    """
    Same as `highlight_content()` however is wrapped in Quart's `run_sync()`
    decorator to ensure event loop is not blocked

        :param content: The content to highlight
        :param lexer_name: The lexer to use
        :return: The highlighted content as html
    """
    return highlight_content(content, lexer_name)


def make_default_expires_at(settings: ExpireTimeDefaultSettings) -> datetime | None:
    if settings.ENABLE:
        default_expires_at = datetime.now()
        default_expires_at += timedelta(
            minutes=settings.MINUTES,
            hours=settings.HOURS,
            days=settings.DAYS,
        )
        return default_expires_at
