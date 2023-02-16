import logging
from datetime import datetime, timedelta

from pydantic import BaseModel, ValidationError, validator

from . import renderer, json


logger = logging.getLogger("paste_bin")

CURRENT_PASTE_META_VERSION = 1


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
            :raises PasteMetaVersionInvalid: Raised when the meta version
                                             is detected to be unsupported
            :raises PasteMetaUnprocessable: Raised when the meta is not valid
            :return: The valid meta object
        """
        try:
            version = PasteMetaVersion.parse_raw(line).version
            # NOTE this allows for future support if the meta format was to change
            if version != CURRENT_PASTE_META_VERSION:
                raise PasteMetaVersionInvalid(
                    f"paste is not a valid version number of '{version}'")
            return PasteMeta.parse_raw(line)
        except ValidationError as err:
            raise PasteMetaUnprocessable(
                f"paste meta validation did not pass: '{line}'") from err

    def until_expiry(self) -> timedelta | None:
        """
        Returns the calculated timedelta from current UTC datetime,
        or None if expiry has not been set
        """
        if self.expire_dt:
            now = datetime.utcnow()
            remaining = self.expire_dt - now
            return remaining

    class Config:
        json_loads = json.loads
        json_dumps = json.dumps


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

    class Config:
        json_loads = json.loads
        json_dumps = json.dumps


class PasteApiCreate(BaseModel):
    content: str
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

    class Config:
        json_loads = json.loads
        json_dumps = json.dumps
