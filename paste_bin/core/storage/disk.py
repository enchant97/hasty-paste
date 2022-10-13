import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from aiofiles import open as aio_open
from aiofiles import os as aio_os
from aiofiles import ospath as aio_ospath
from quart import Quart

from ... import helpers
from .base import BaseStorage

logger = logging.getLogger("paste_bin")


class DiskStorage(BaseStorage):
    def __init__(self, app: Quart, paste_root: Path, **kw):
        self._paste_root = paste_root

    @staticmethod
    async def _is_on_disk(paste_path: Path) -> bool:
        return await aio_ospath.isfile(paste_path)

    def _create_paste_path(self, paste_id: str, mkdir: bool = False) -> Path:
        """
        Combines a the paste root with a paste's id to form the full path.
        Will also optionally ensure the directories are created

            :param paste_id: The paste's id
            :param mkdir: Creates the directories if not found, defaults to False
            :raises PasteIdException: If the given id was invalid
            :return: The combined path
        """
        if len(paste_id) < 3:
            raise helpers.PasteIdException(
                "paste_id too short, must be at least 3 characters long")
        full_path = self._paste_root / paste_id[:2]
        if mkdir:
            full_path.mkdir(parents=True, exist_ok=True)
        return full_path / paste_id[2:]

    async def write_paste(
            self,
            paste_id: str,
            raw: AsyncGenerator[bytes, None] | bytes,
            meta: helpers.PasteMeta):
        """
        Writes a new paste

            :param paste_id: The paste's id
            :param raw: The paste's raw content
            :param meta: The pastes meta
        """
        paste_path = self._create_paste_path(paste_id, True)

        async with aio_open(paste_path, "wb") as fo:
            await fo.write(meta.json().encode() + b"\n")
            if isinstance(raw, bytes):
                await fo.write(raw)
            else:
                async for chunk in raw:
                    await fo.write(chunk)

    async def read_paste_meta(self, paste_id: str) -> helpers.PasteMeta | None:
        paste_path = self._create_paste_path(paste_id, False)

        if not await self._is_on_disk(paste_path):
            logger.debug("paste id of '%s' not found on filesystem", paste_id)
            return

        async with aio_open(paste_path, "rb") as fo:
            meta = helpers.extract_paste_meta(await fo.readline())
            return meta

    async def read_paste_raw(self, paste_id: str) -> bytes | None:
        """
        Read the paste's raw content from disk

            :param paste_id: The paste's id
            :return: The paste content as bytes
        """
        paste_path = self._create_paste_path(paste_id, False)

        if not await self._is_on_disk(paste_path):
            logger.debug("paste id of '%s' not found on filesystem", paste_id)
            return

        async with aio_open(paste_path, "rb") as fo:
            # TODO use tell+seek+read to save memory while checking for newline
            _ = await fo.readline()
            raw_paste = await fo.read()
        return raw_paste

    async def delete_paste(self, paste_id: str):
        paste_path = self._create_paste_path(paste_id, False)
        logger.debug("auto removing of paste with id of '%s'", paste_id)
        try:
            await aio_os.remove(paste_path)
        except FileNotFoundError:
            pass