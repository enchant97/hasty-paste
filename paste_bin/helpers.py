import logging
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps

from pydantic import BaseModel, ValidationError, validator
from quart import abort
from werkzeug.routing import BaseConverter

from paste_bin.core.paste_handler import PasteHandlerException

from .config import ExpireTimeDefaultSettings
from .core import renderer

logger = logging.getLogger("paste_bin")

PASTE_ID_CHARACTER_SET = string.ascii_letters + string.digits
CURRENT_PASTE_META_VERSION = 1
VALID_PASTE_ID_REGEX = r"[a-zA-Z0-9]+"


class OptionalRequirementMissing(Exception):
    pass


class PasteMetaException(Exception):
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

    @classmethod
    def extract_from_line(cls, line: str | bytes) -> "PasteMeta":
        """
        Processes a meta line and converts it into a object.

            :param meta_line: The meta line to process
            :raises PasteMetaVersionInvalid: Raised when the meta version is detected to be unsupported
            :raises PasteMetaUnprocessable: Raised when the meta is not valid
            :return: The valid meta object
        """
        try:
            version = PasteMetaVersion.parse_raw(line).version
            # NOTE this allows for future support if the meta format was to change
            if version != CURRENT_PASTE_META_VERSION:
                logger.error(
                    "failed to load paste meta, version not supported: '%s'", line)
                raise PasteMetaVersionInvalid(
                    f"paste is not a valid version number of '{version}'")
            return PasteMeta.parse_raw(line)
        except ValidationError as err:
            logger.error(
                "failed to load paste meta, validation did not pass: '%s'", line)
            raise PasteMetaUnprocessable("paste meta cannot be loaded") from err


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


def handle_known_exceptions(func):
    """
    Used as a decorator,
    to handle known exceptions
    that may happen during a request/response
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PasteHandlerException:
            logger.exception("catching PasteHandlerException in request and aborting with 500")
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


class PasteIdConverter(BaseConverter):
    regex = VALID_PASTE_ID_REGEX
    part_isolating = True
