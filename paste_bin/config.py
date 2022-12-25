from functools import cache
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, BaseSettings, validator, SecretStr
from pytz import all_timezones_set


class StorageTypes(str, Enum):
    DISK = "DISK"
    S3 = "S3"


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
    USE_LONG_ID: bool | None = False
    EXPIRE_TIME: ExpireTimeDefaultSettings = ExpireTimeDefaultSettings()


class CacheSettings(BaseModel):
    ENABLE: bool = True
    INTERNAL_MAX_SIZE: int = 4
    REDIS_URI: SecretStr | None = None


class DiskStorageSettings(BaseModel):
    PASTE_ROOT: Path | None = None


class S3StorageSettings(BaseModel):
    ENDPOINT_URL: str | None = None
    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: SecretStr | None = None
    BUCKET_NAME: str = "hasty-paste"

    def to_boto3_config(self):
        return {
            "endpoint_url": self.ENDPOINT_URL,
            "aws_access_key_id": self.ACCESS_KEY_ID,
            "aws_secret_access_key": self.SECRET_ACCESS_KEY.get_secret_value(),
        }


class StorageSettings(BaseModel):
    TYPE: StorageTypes = StorageTypes.DISK
    DISK: DiskStorageSettings = DiskStorageSettings()
    S3: S3StorageSettings = S3StorageSettings()

    def ensure_valid(self):
        if self.TYPE == StorageTypes.DISK:
            if not self.DISK.PASTE_ROOT:
                raise ValueError("PASTE_ROOT must be defined")
        elif self.TYPE == StorageTypes.S3:
            if not self.S3.ACCESS_KEY_ID:
                raise ValueError("ACCESS_KEY_ID must be defined")
            if not self.S3.SECRET_ACCESS_KEY:
                raise ValueError("SECRET_ACCESS_KEY must be defined")
        else:
            raise ValueError("unhandled storage type")


class Settings(BaseSettings):
    TIME_ZONE: str = "Europe/London"
    NEW_AT_INDEX: bool = False
    ENABLE_PUBLIC_LIST: bool = False
    UI_DEFAULT: DefaultsSettings = DefaultsSettings()
    BRANDING: BrandSettings = BrandSettings()
    STORAGE: StorageSettings = StorageSettings()
    CACHE: CacheSettings = CacheSettings()

    MAX_BODY_SIZE: int = 2*(10**6)
    LOG_LEVEL: str = "WARNING"

    @validator("TIME_ZONE")
    def validate_time_zone(cls, time_zone: str):
        if time_zone not in all_timezones_set:
            raise ValueError("not valid timezone")
        return time_zone

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'
        use_enum_values = True


@cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
