from .base import BaseCache


class FakeCache(BaseCache):
    """
    This cache will never do any caching
    """
    def __init__(self, app, **kw):
        pass

    async def push_paste_all(self, paste_id, /, *, meta=None, html=None, raw=None):
        pass

    async def push_paste_meta(self, paste_id, meta):
        pass

    async def get_paste_meta(self, paste_id):
        pass

    async def get_paste_rendered(self, paste_id):
        pass

    async def get_paste_raw(self, paste_id):
        pass
