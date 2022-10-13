import logging
import secrets
import string
from collections.abc import Generator
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from pydantic import BaseModel, ValidationError, validator
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (find_lexer_class_by_name, get_all_lexers,
                             get_lexer_by_name)
from pygments.util import ClassNotFound as PygmentsClassNotFound
from quart import Response, abort, make_response
from quart.utils import run_sync
from werkzeug.routing import BaseConverter
from werkzeug.wrappers import Response as WerkzeugResponse

from .config import ExpireTimeDefaultSettings

logger = logging.getLogger("paste_bin")

PASTE_ID_CHARACTER_SET = string.ascii_letters + string.digits
CURRENT_PASTE_META_VERSION = 1
VALID_PASTE_ID_REGEX = r"[a-zA-Z0-9]+"


class OptionalRequirementMissing(Exception):
    pass


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
            raise PasteExpiredException(
                f"paste has expired with id of {self.paste_id}")


class PasteMetaToCreate(BaseModel):
    expire_dt: datetime | None = None
    lexer_name: str | None = None
    title: str | None = None

    def into_meta(self, paste_id: str) -> PasteMeta:
        return PasteMeta(
            paste_id=paste_id,
            creation_dt=datetime.utcnow(),
            **self.dict(),
        )

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


def extract_paste_meta(meta_line: str | bytes) -> PasteMeta:
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
            logger.error(
                "failed to load paste meta, version not supported: '%s'", meta_line)
            raise PasteMetaVersionInvalid(
                f"paste is not a valid version number of '{version}'")
        return PasteMeta.parse_raw(meta_line)
    except ValidationError as err:
        logger.error(
            "failed to load paste meta, validation did not pass: '%s'", meta_line)
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


def get_form_datetime(value: str | None) -> datetime | None:
    """
    Handle loading a datetime from form input

        :param value: The form value
        :return: The processed datetime or None
    """
    if value:
        return datetime.fromisoformat(value)


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
            logger.debug(
                "skipping code highlighting as no lexer was found by '%s'", lexer_name)

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


class PasteIdConverter(BaseConverter):
    regex = VALID_PASTE_ID_REGEX
    part_isolating = True
