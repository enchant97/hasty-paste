import logging
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps

from quart import abort
from werkzeug.routing import BaseConverter, ValidationError

from ..config import ExpireTimeDefaultSettings

logger = logging.getLogger("paste_bin")

PASTE_ID_CHARACTER_SET = string.ascii_letters + string.digits
VALID_PASTE_ID_REGEX = r"[a-zA-Z0-9]+"
PASTE_ID_SHORT_LEN = 10
PASTE_ID_LONG_LEN = 40


class OptionalRequirementMissing(Exception):
    pass


class PasteHandlerException(Exception):
    pass


class PasteHandlerStorageException(Exception):
    pass


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
        return gen_id(PASTE_ID_LONG_LEN)
    return gen_id(PASTE_ID_SHORT_LEN)


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

    def to_python(self, value: str) -> str:
        if len(value) not in (PASTE_ID_SHORT_LEN, PASTE_ID_LONG_LEN):
            raise ValidationError()
        return value
