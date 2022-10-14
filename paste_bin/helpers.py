import logging
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps

import pytz
from pydantic import BaseModel, ValidationError, validator
from quart import abort
from werkzeug.routing import BaseConverter

from .config import ExpireTimeDefaultSettings
from .core import renderer

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

class PasteApiCreate(BaseModel):
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
        if lexer_name is not None and not renderer.is_valid_lexer_name(lexer_name):
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


def get_form_datetime(value: str | None) -> datetime | None:
    """
    Handle loading a datetime from form input

        :param value: The form value
        :return: The processed datetime or None
    """
    if value:
        return datetime.fromisoformat(value)


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


def make_default_expires_at(settings: ExpireTimeDefaultSettings) -> datetime | None:
    """
    Get expiry time, in UTC
    """
    if settings.ENABLE:
        default_expires_at = datetime.utcnow()
        default_expires_at += timedelta(
            minutes=settings.MINUTES,
            hours=settings.HOURS,
            days=settings.DAYS,
        )
        return default_expires_at


def utc_to_local(v: datetime, timezone: str) -> datetime:
    """
    convert utc time into given local timezone,
    will return datetime without a tzinfo
    """
    time_zone = pytz.timezone(timezone)
    return pytz.utc.localize(v).astimezone(time_zone).replace(tzinfo=None)


def local_to_utc(v: datetime, timezone: str) -> datetime:
    """
    convert datetime from given local timzone into utc,
    will return datetime without a tzinfo
    """
    time_zone = pytz.timezone(timezone)
    return time_zone.localize(v).astimezone(pytz.utc).replace(tzinfo=None)


class PasteIdConverter(BaseConverter):
    regex = VALID_PASTE_ID_REGEX
    part_isolating = True
