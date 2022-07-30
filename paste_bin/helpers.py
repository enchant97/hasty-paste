import secrets
from collections.abc import AsyncGenerator
from datetime import datetime
from functools import wraps
from pathlib import Path

from aiofiles import open as aio_open
from aiofiles import os as aio_os
from aiofiles import ospath as aio_ospath
from pydantic import BaseModel, ValidationError
from quart import Response, abort, make_response

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

    @property
    def is_expired(self) -> bool:
        if self.expire_dt is not None and self.expire_dt < datetime.utcnow():
            return True
        return False


class PasteMetaCreate(BaseModel):
    content: bytes
    long_id: bool = False
    expire_dt: datetime | None = None


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
            raise PasteMetaVersionInvalid(f"paste is not a valid version number of '{version}'")
        return PasteMeta.parse_raw(meta_line)
    except ValidationError as err:
        raise PasteMetaUnprocessable("paste meta cannot be loaded") from err


def create_paste_id(long: bool = False) -> str:
    """
    Creates a paste id, if in 'long' mode will
    generate a very long id meant to
    reduce chance of a brute force attack

        :param long: Whether to use the long id, defaults to False
        :return: The generated id
    """
    if long:
        return secrets.token_urlsafe(30)
    return secrets.token_urlsafe(7)


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


async def write_paste(
        paste_path: Path,
        paste_meta: PasteMeta,
        content: AsyncGenerator[bytes, None] | bytes):
    """
    Writes a new paste

        :param paste_path: The full paste path
        :param paste_meta: The pastes meta
        :param content: The paste content
    """
    async with aio_open(paste_path, "wb") as fo:
        await fo.write(paste_meta.json().encode() + b"\n")
        if isinstance(content, AsyncGenerator):
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


def get_form_datetime(value: str) -> datetime | None:
    """
    Handle loading a datetime from form input

        :param value: The form value
        :return: The processed datetime or None
    """
    if value:
        return datetime.fromisoformat(value)


async def try_get_paste(
        root_path: Path,
        paste_id: str,
        auto_remove: bool = True,
        ) -> tuple[Path, PasteMeta]:
    """
    Try to process the paste meta

        :param root_path: The root path
        :param paste_id: The paste's id
        :param auto_remove: Whether to auto remove the paste on expiry, defaults to True
        :raises PasteDoesNotExistException: When the paste is not found
        :raises PasteExpiredException: When the paste has expired
        :return: The paste's full path and it's loaded meta
    """
    paste_path = create_paste_path(root_path, paste_id)

    if not await aio_ospath.isfile(paste_path):
        raise PasteDoesNotExistException(f"paste not found with id of {paste_id}")

    paste_meta = await read_paste_meta(paste_path)

    if paste_meta.is_expired:
        if auto_remove:
            try:
                await aio_os.remove(paste_path)
            except FileNotFoundError:
                pass
        raise PasteExpiredException(f"paste has expired with id of {paste_id}")

    return paste_path, paste_meta


async def try_get_paste_with_content_response(
        root_path: Path,
        paste_id: str,
        auto_remove: bool = True,
        ) -> tuple[Path, PasteMeta, Response]:
    """
    An extension of `try_get_paste()`,
    will also return the paste contents in a response

        :param root_path: The root path
        :param paste_id: The paste's id
        :param auto_remove: Whether to auto remove the paste on expiry, defaults to True
        :return: The paste's full path, it's meta and the content response
    """
    paste_path, paste_meta = await try_get_paste(root_path, paste_id, auto_remove)

    response = await make_response(read_paste_content(paste_path))
    response.mimetype = "text/plain"

    return paste_path, paste_meta, response


def handle_paste_exceptions(func):
    """
    Used as a decorator, to handle
    `PasteException` and `PasteMetaException` errors
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PasteException:
            abort(404)
        except PasteMetaException:
            abort(500)
    return wrapper
