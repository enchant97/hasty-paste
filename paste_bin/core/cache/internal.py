import logging
from collections import OrderedDict
from dataclasses import dataclass

from ..models import PasteMeta
from .base import BaseCache

logger = logging.getLogger("paste_bin")


@dataclass
class InternalCacheItem:
    meta: PasteMeta | None = None
    rendered_paste: str | None = None
    raw_paste: bytes | None = None


class InternalCache(BaseCache):
    """
    Basic internal cache, that does not need a separate service
    """
    _max_meta_size: int
    _cache: OrderedDict[str, InternalCacheItem]

    def __init__(self, *, fallback=None, max_size: int = 5, **kw):
        super().__init__(fallback=fallback)

        self._max_meta_size = max_size
        self._cache = OrderedDict()

    @property
    def cache_len(self) -> int:
        """
        returns how many items are in cache
        """
        return len(self._cache)

    def _expire_old(self):
        if self.cache_len > self._max_meta_size:
            # remove all that are least accessed
            n_to_removed = self.cache_len - self._max_meta_size
            logger.debug("removing %s oldest items from cache", n_to_removed)
            [self._cache.popitem(last=True) for _ in range(n_to_removed)]

    def _read_cache(self, paste_id: str) -> InternalCacheItem | None:
        if (cached := self._cache.get(paste_id)) is not None:
            # we want most used items at front, so least accessed are removed first
            self._cache.move_to_end(paste_id, last=False)
            return cached

    def _write_cache(self, paste_id: str, to_cache: InternalCacheItem):
        # insert/overwrite cache
        self._cache[paste_id] = to_cache
        # we want most used items at front
        self._cache.move_to_end(paste_id, last=False)
        # expire old items
        self._expire_old()

    async def push_paste_any(
            self,
            paste_id,
            /, *,
            meta=None,
            html=None,
            raw=None,
            update_fallback: bool = True):
        if meta is None and html is None and raw is None:
            # don't bother if everything is None
            return
        # get existing cache item (if it exists)
        existing = self._read_cache(paste_id)
        if not existing:
            # create blank cache item
            existing = InternalCacheItem()
        # merge new cache item with existing, if possible
        to_cache = InternalCacheItem(
            meta=meta if meta else existing.meta,
            rendered_paste=html if html else existing.rendered_paste,
            raw_paste=raw if raw else existing.raw_paste,
        )
        self._write_cache(paste_id, to_cache)

        if self._fallback and update_fallback:
            await self._fallback.push_paste_any(paste_id, meta=meta, html=html, raw=raw)

    async def get_paste_meta(self, paste_id):
        cached = self._read_cache(paste_id)
        cached = None if cached is None else cached.meta
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_meta(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, meta=cached, update_fallback=False)
        return cached

    async def get_paste_rendered(self, paste_id):
        cached = self._read_cache(paste_id)
        cached = None if cached is None else cached.rendered_paste
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_rendered(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, html=cached, update_fallback=False)
        return cached

    async def get_paste_raw(self, paste_id):
        cached = self._read_cache(paste_id)
        cached = None if cached is None else cached.raw_paste
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_raw(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, raw=cached, update_fallback=False)
        return cached

    async def remove_paste(self, paste_id: str):
        self._cache.pop(paste_id, None)
        if self._fallback:
            await self._fallback.remove_paste(paste_id)
