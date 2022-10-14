import logging
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

from aiofiles import open as aio_open
from aiofiles import os as aio_os
from aiofiles import ospath as aio_ospath

from ..models import PasteMeta
from .base import BaseStorage
from .exceptions import StorageReadException, StorageWriteException

logger = logging.getLogger("paste_bin")


def get_all_paste_id_parts(root_path: Path) -> Generator[str, None, None]:
    """
    Yields each paste id part found

        :param root_path: The root pastes path
        :yield: A pastes id part
    """
    for part in root_path.glob("*"):
        yield part.name


def get_all_paste_ids_from_part(root_path: Path, id_part: str) -> Generator[str, None, None]:
    """
    Yield each paste id from a id part directory

        :param root_path: The root pastes path
        :param id_part: The id part
        :yield: The full paste id
    """
    for part in root_path.joinpath(id_part).glob("*"):
        yield id_part + part.name


def get_all_paste_ids(root_path: Path) -> Generator[str, None, None]:
    for id_part in get_all_paste_id_parts(root_path):
        for full_id in get_all_paste_ids_from_part(root_path, id_part):
            yield full_id


class DiskStorage(BaseStorage):
    def __init__(self, paste_root: Path, **kw):
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
            :raises StorageWriteException: Directoy could not to be created
            :return: The combined path
        """
        if len(paste_id) < 3:
            # NOTE this should never happen!
            raise ValueError(
                "paste_id too short, must be at least 3 characters long")
        full_path = self._paste_root / paste_id[:2]
        if mkdir:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
            except PermissionError as err:
                raise StorageWriteException("failed to create paste directory") from err
        return full_path / paste_id[2:]

    async def write_paste(
            self,
            paste_id: str,
            raw: AsyncGenerator[bytes, None] | bytes,
            meta: PasteMeta):
        """
        Writes a new paste

            :param paste_id: The paste's id
            :param raw: The paste's raw content
            :param meta: The pastes meta
        """
        paste_path = self._create_paste_path(paste_id, True)

        try:
            async with aio_open(paste_path, "wb") as fo:
                await fo.write(meta.json().encode() + b"\n")
                if isinstance(raw, bytes):
                    await fo.write(raw)
                else:
                    async for chunk in raw:
                        await fo.write(chunk)
        except PermissionError as err:
            raise StorageWriteException(f"failed to write paste data for '{paste_id}'") from err

    async def read_paste_meta(self, paste_id: str) -> PasteMeta | None:
        paste_path = self._create_paste_path(paste_id, False)

        if not await self._is_on_disk(paste_path):
            logger.debug("paste id of '%s' not found on filesystem", paste_id)
            return

        try:
            async with aio_open(paste_path, "rb") as fo:
                meta = PasteMeta.extract_from_line(await fo.readline())
                return meta
        except PermissionError as err:
            raise StorageReadException(f"failed to read paste meta for '{paste_id}'") from err

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

        try:
            async with aio_open(paste_path, "rb") as fo:
                # TODO use tell+seek+read to save memory while checking for newline
                _ = await fo.readline()
                raw_paste = await fo.read()
                return raw_paste
        except PermissionError as err:
            raise StorageReadException(f"failed to read paste raw for '{paste_id}'") from err

    async def read_all_paste_ids(self) -> AsyncGenerator[str, None]:
        try:
            for paste_id in get_all_paste_ids(self._paste_root):
                yield paste_id
        except PermissionError as err:
            raise StorageReadException(f"failed to get directory contents of pastes") from err

    async def delete_paste(self, paste_id: str):
        paste_path = self._create_paste_path(paste_id, False)
        logger.debug("auto removing of paste with id of '%s'", paste_id)
        try:
            await aio_os.remove(paste_path)
        except FileNotFoundError:
            pass
        except PermissionError as err:
            raise StorageWriteException(f"failed to delete paste '{paste_id}'") from err
