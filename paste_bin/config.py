from functools import cache
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    PASTE_ROOT: Path
    NEW_AT_INDEX: bool = False
    ENABLE_PUBLIC_LIST: bool = False
    DEFAULT_EXPIRE_TIME: bool = False
    DEFAULT_EXPIRE_TIME__MINUTES: int = 0
    DEFAULT_EXPIRE_TIME__HOURS: int = 1
    DEFAULT_EXPIRE_TIME__DAYS: int = 0

    MAX_BODY_SIZE: int = 2*(10**6)
    LOG_LEVEL: str = "WARNING"

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'


@cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
