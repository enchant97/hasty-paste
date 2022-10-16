import logging

from quart import Quart

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None

from ..helpers import OptionalRequirementMissing
from ..models import PasteMeta
from .base import BaseCache

logger = logging.getLogger("paste_bin")


class RedisCache(BaseCache):
    _conn: Redis

    def __init__(
            self,
            *,
            fallback=None,
            app: Quart | None = None,
            redis_url: str | None = None,
            **kw):
        super().__init__(fallback=fallback)

        self._conn = None

        if app is None or redis_url is None:
            raise ValueError("'app' or 'redis_url' cannot be None")

        if Redis is None:
            raise OptionalRequirementMissing(
                "redis requirement must be installed for redis cache"
            )

        @app.while_serving
        async def handle_lifespan():
            logger.info("connecting to redis...")
            self._conn = Redis.from_url(redis_url)
            logger.info("connected to redis")
            yield
            logger.info("closing redis connection...")
            await self._conn.close()
            logger.info("closed redis connection")

    async def push_paste_any(self, paste_id, /, *, meta=None, html=None, raw=None):
        to_cache = {}

        if meta:
            to_cache[f"{paste_id}__meta"] = meta.json()
        if html:
            to_cache[f"{paste_id}__html"] = html
        if raw:
            to_cache[f"{paste_id}__raw"] = raw

        await self._conn.mset(to_cache)

        if self._fallback:
            await self._fallback.push_paste_any(paste_id, meta=meta, html=html, raw=raw)

    async def get_paste_meta(self, paste_id):
        cached = await self._conn.get(f"{paste_id}__meta")
        if cached:
            cached = PasteMeta.parse_raw(cached)
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_meta(paste_id)
        return cached

    async def get_paste_rendered(self, paste_id):
        cached = await self._conn.get(f"{paste_id}__html")
        if cached:
            cached = cached.decode()
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_rendered(paste_id)
        return cached

    async def get_paste_raw(self, paste_id):
        cached = await self._conn.get(f"{paste_id}__raw")
        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_raw(paste_id)
        return cached

    async def remove_paste(self, paste_id: str):
        await self._conn.delete(
            f"{paste_id}__meta",
            f"{paste_id}__html",
            f"{paste_id}__raw",
        )
