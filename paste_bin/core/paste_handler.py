import logging
from collections.abc import AsyncGenerator
from typing import cast

from quart import current_app
from quart.wrappers import Body

from .. import helpers
from .cache import BaseCache
from .storage import BaseStorage

ASYNC_BYTES_GEN_TYPE = AsyncGenerator[bytes, None]

logger = logging.getLogger("paste_bin")


class PasteHandler:
    """
    Class responsible for handling access to pastes from 'disk' & cache when possible
    """
    def __init__(self, storage: BaseStorage, cache: BaseCache):
        self._storage = storage
        self._cache = cache

    def __run_in_background(self, func, *args, **kwargs):
        current_app.add_background_task(func, *args, **kwargs)

    async def create_paste(
            self,
            long_id: bool,
            raw: AsyncGenerator[bytes, None] | Body | bytes,
            config: helpers.PasteMetaToCreate) -> str:
        """
        Create a new paste

            :param raw: The raw paste content
            :param config: The paste's config (meta without id)
            :return: The created paste's id
        """
        paste_id = helpers.create_paste_id(long_id)
        meta = config.into_meta(paste_id)
        await self._storage.write_paste(paste_id, cast(ASYNC_BYTES_GEN_TYPE, raw), meta)
        self.__run_in_background(self._cache.push_paste_any, paste_id, meta=meta)
        return paste_id

    async def get_paste_meta(self, paste_id: str) -> helpers.PasteMeta | None:
        """
        Gets the paste's meta

            :param paste_id: The paste's id
            :return: The paste's meta
        """
        if (meta := await self._cache.get_paste_meta(paste_id)) is not None:
            logger.debug("cache hit for meta-'%s'", paste_id)
            return meta
        if (meta := await self._storage.read_paste_meta(paste_id)) is not None:
            logger.debug("cache miss for meta-'%s'", paste_id)
            self.__run_in_background(self._cache.push_paste_any, paste_id, meta=meta)
            return meta

    async def get_paste_raw(self, paste_id: str) -> bytes | None:
        """
        Gets a paste's raw content

            :param paste_id: The paste's id
            :return: The paste's raw content
        """
        if (raw := await self._cache.get_paste_raw(paste_id)) is not None:
            return raw
        if (raw := await self._storage.read_paste_raw(paste_id)) is not None:
            return raw

    async def get_paste_rendered(
            self,
            paste_id: str,
            custom_lexer: str | None = None) -> str | None:
        """
        Gets a paste's rendered raw content

            :param paste_id: The paste's id
            :param custom_lexer: Whether to override the lexer, defaults to None
            :return: The rendered content
        """
        if (
                custom_lexer is None and
                (rendered := await self._cache.get_paste_rendered(paste_id)) is not None):
            logger.debug("cache hit for rendered-'%s'", paste_id)
            return rendered
        meta = await self.get_paste_meta(paste_id)
        # no meta means it does not exist
        if meta is None:
            return
        if (raw := await self.get_paste_raw(paste_id)) is not None:
            logger.debug("cache miss for rendered-'%s'", paste_id)
            lexer_name = custom_lexer or meta.lexer_name or "text"
            rendered = await helpers.highlight_content_async_wrapped(
                raw.decode(),
                lexer_name,
            )
            # HACK override lexer content cannot be cached, should be fixed in 1.7
            if custom_lexer is None:
                await self._cache.push_paste_any(paste_id, html=rendered)
            return rendered

    def get_all_paste_ids(self) -> AsyncGenerator[str, None]:
        return self._storage.read_all_paste_ids()

    async def get_all_paste_ids_as_csv(self) -> AsyncGenerator[str, None]:
        async for paste_id in self.get_all_paste_ids():
            yield paste_id + "\n"

    async def remove_paste(self, paste_id: str):
        """
        Remove a paste, for example used when a paste has expired

            :param paste_id: The paste's id
        """
        self.__run_in_background(self._storage.delete_paste, paste_id)


loaded_handler = None


def init_handler(handler: PasteHandler):
    global loaded_handler
    loaded_handler = handler


def get_handler() -> PasteHandler:
    return loaded_handler  # type: ignore
