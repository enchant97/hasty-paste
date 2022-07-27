import secrets
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from aiofiles import open as aio_open
from pydantic import BaseModel


class PasteMeta(BaseModel):
    paste_id: str
    creation_dt: datetime
    expire_dt: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expire_dt is not None and self.expire_dt < datetime.utcnow():
            return True
        return False


def get_paste_meta(meta_line: bytes) -> PasteMeta:
    return PasteMeta.parse_raw(meta_line)


def create_paste_id(long: bool = False) -> str:
    if long:
        return secrets.token_hex(20)
    return secrets.token_hex(5)


def create_paste_path(root_path: Path, paste_id: str, mkdir: bool = False) -> Path:
    if len(paste_id) < 3:
        raise ValueError("paste_id too short, must be at least 3 characters long")
    full_path = root_path / paste_id[:2]
    if mkdir:
        full_path.mkdir(parents=True, exist_ok=True)
    return full_path / paste_id[2:]


async def write_paste(
        paste_path: Path,
        paste_meta: PasteMeta,
        content: AsyncGenerator[bytes, None] | bytes):
    async with aio_open(paste_path, "wb") as fo:
        await fo.write(paste_meta.json().encode() + b"\n")
        if isinstance(content, AsyncGenerator):
            async for chunk in content:
                await fo.write(chunk)
        else:
            await fo.write(content)


async def read_paste_meta(paste_path: Path) -> PasteMeta:
    async with aio_open(paste_path, "rb") as fo:
        meta = get_paste_meta(await fo.readline())
        return meta


async def read_paste_content(paste_path: Path) -> AsyncGenerator[bytes, None]:
    async with aio_open(paste_path, "rb") as fo:
        # TODO use tell+seek+read to save memory while checking for newline
        _ = await fo.readline()
        async for line in fo:
            yield line


def get_form_datetime(value: str) -> datetime | None:
    if value:
        return datetime.fromisoformat(value)
