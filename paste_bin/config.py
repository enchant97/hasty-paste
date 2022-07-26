from functools import cache
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    PASTE_ROOT: Path


@cache
def get_settings() -> Settings:
    return Settings()
