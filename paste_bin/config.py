from functools import cache
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    PASTE_ROOT: Path
    MAX_BODY_SIZE: int = 2*(10**6)
    LOG_LEVEL: str = "WARNING"

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'


@cache
def get_settings() -> Settings:
    return Settings()
