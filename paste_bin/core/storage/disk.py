import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from aiofiles import ospath as aio_ospath
from quart import Quart

from ... import helpers
from .base import BaseStorage

logger = logging.getLogger("paste_bin")


class DiskStorage(BaseStorage):
    def __init__(self, app: Quart, paste_root: Path, **kw):
        self._paste_root = paste_root

    def create_paste_path(self, paste_id: str, mkdir: bool = False) -> Path:
        return helpers.create_paste_path(self._paste_root, paste_id, mkdir)

    async def write_paste(
            self,
            paste_id: str,
            raw: AsyncGenerator[bytes, None] | bytes,
            meta: helpers.PasteMeta):
        paste_path = self.create_paste_path(paste_id, True)
        await helpers.write_paste(paste_path, meta, raw)

    async def read_paste_meta(self, paste_id: str) -> helpers.PasteMeta | None:
        paste_path = self.create_paste_path(paste_id, True)
        if not await aio_ospath.isfile(paste_path):
            logger.info("paste id of '%s' not found on filesystem", paste_id)
            return
        return await helpers.read_paste_meta(paste_path)

    async def read_paste_raw(self, paste_id: str) -> bytes | None:
        paste_path = self.create_paste_path(paste_id, True)
        raw_paste = helpers.read_paste_content(paste_path)
        raw_paste = b"".join([line async for line in raw_paste])
        return raw_paste

    async def delete_paste(self, paste_id: str):
        paste_path = self.create_paste_path(paste_id, True)
        await helpers.safe_remove_paste(paste_path, paste_id)
