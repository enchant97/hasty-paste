from functools import cache
from pathlib import Path

from pydantic import BaseModel, BaseSettings


class BrandSettings(BaseModel):
    TITLE: str = "Hasty Paste"
    DESCRIPTION: str = "A fast and minimal paste bin."
    ICON: Path | None = None
    FAVICON: Path | None = None
    CSS_FILE: Path | None = None
    HIDE_VERSION: bool = False


class ExpireTimeDefaultSettings(BaseModel):
    ENABLE: bool = False
    MINUTES: int = 0
    HOURS: int = 1
    DAYS: int = 0


class DefaultsSettings(BaseModel):
    USE_LONG_ID: bool | None = None
    EXPIRE_TIME: ExpireTimeDefaultSettings = ExpireTimeDefaultSettings()


class CacheSettings(BaseModel):
    ENABLE: bool = True
    MAX_INTERNAL_SIZE: int = 4
    REDIS_URI: str | None = None


class Settings(BaseSettings):
    PASTE_ROOT: Path
    NEW_AT_INDEX: bool = False
    ENABLE_PUBLIC_LIST: bool = False
    UI_DEFAULT: DefaultsSettings = DefaultsSettings()
    BRANDING: BrandSettings = BrandSettings()
    CACHE: CacheSettings = CacheSettings()

    MAX_BODY_SIZE: int = 2*(10**6)
    LOG_LEVEL: str = "WARNING"

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'


@cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
