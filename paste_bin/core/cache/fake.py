from .base import BaseCache


class FakeCache(BaseCache):
    """
    This cache will never do any caching.
    If a fallback is provided, will always use that
    """

    def __init__(self, *, fallback=None, **kw):
        super().__init__(fallback=fallback)

    async def push_paste_any(
            self,
            paste_id,
            /, *,
            meta=None,
            html=None,
            raw=None,
            update_fallback: bool = True):
        if self._fallback and update_fallback:
            await self._fallback.push_paste_any(paste_id, meta=meta, html=html, raw=raw)

    async def get_paste_meta(self, paste_id):
        if self._fallback:
            return await self._fallback.get_paste_meta(paste_id)

    async def get_paste_rendered(self, paste_id):
        if self._fallback:
            return await self._fallback.get_paste_rendered(paste_id)

    async def get_paste_raw(self, paste_id):
        if self._fallback:
            return await self._fallback.get_paste_raw(paste_id)

    async def remove_paste(self, paste_id: str):
        if self._fallback:
            await self._fallback.remove_paste(paste_id)
