import logging
from collections import OrderedDict
from dataclasses import dataclass

from .helpers import PasteMeta

logger = logging.getLogger("paste_bin")


@dataclass
class InternalCacheItem:
    meta: PasteMeta
    rendered_paste: str | None = None
    raw_paste: bytes | None = None


# TODO inherit from a base class, for adding different cache types
class InternalCache:
    """
    Basic internal cache, that does not need a separate service
    """
    _max_meta_size: int
    _cache: OrderedDict[str, InternalCacheItem]

    def __init__(self, max_size: int):
        self._max_meta_size = max_size
        self._cache = OrderedDict()

    @property
    def cache_len(self) -> int:
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

    def push_paste_all(
            self,
            paste_id: str,
            meta: PasteMeta | None = None,
            html: str | None = None,
            raw: bytes | None = None):
        # take value of existing cache if None
        meta = meta if meta is not None else self.get_paste_meta(paste_id)
        html = html if html is not None else self.get_paste_rendered(paste_id)
        raw = raw if raw is not None else self.get_paste_raw(paste_id)
        to_cache = InternalCacheItem(meta=meta, rendered_paste=html, raw_paste=raw)
        self._write_cache(paste_id, to_cache)

    def push_paste_meta(self, paste_id: str, meta: PasteMeta):
        self.push_paste_all(paste_id, meta, None, None)

    def get_paste_meta(self, paste_id: str) -> PasteMeta:
        cached = self._read_cache(paste_id)
        return None if cached is None else cached.meta

    def get_paste_rendered(self, paste_id: str) -> str | None:
        cached = self._read_cache(paste_id)
        return None if cached is None else cached.rendered_paste

    def get_paste_raw(self, paste_id: str) -> bytes | None:
        cached = self._read_cache(paste_id)
        return None if cached is None else cached.raw_paste


loaded_cache = None


def init_cache(cache):
    global loaded_cache
    loaded_cache = cache


def get_cache() -> InternalCache:
    return loaded_cache
