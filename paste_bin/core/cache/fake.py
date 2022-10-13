from .base import BaseCache


class FakeCache(BaseCache):
    """
    This cache will never do any caching
    """
    def __init__(self, **kw):
        pass

    async def push_paste_any(self, paste_id, /, *, meta=None, html=None, raw=None):
        pass

    async def get_paste_meta(self, paste_id):
        pass

    async def get_paste_rendered(self, paste_id):
        pass

    async def get_paste_raw(self, paste_id):
        pass

    async def remove_paste(self, paste_id: str):
        pass
