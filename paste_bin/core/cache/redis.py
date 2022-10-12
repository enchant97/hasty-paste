import logging

from quart import Quart

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None

from ...helpers import OptionalRequirementMissing, PasteMeta
from .base import BaseCache

logger = logging.getLogger("paste_bin")


class RedisCache(BaseCache):
    _conn: Redis

    def __init__(self, app: Quart, redis_url: str):
        self._conn = None

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

    async def push_paste_all(self, paste_id, /, *, meta=None, html=None, raw=None):
        to_cache = {}

        if meta:
            to_cache[f"{paste_id}__meta"] = meta.json()
        if html:
            to_cache[f"{paste_id}__html"] = html
        if raw:
            to_cache[f"{paste_id}__raw"] = raw

        await self._conn.mset(to_cache)

    async def push_paste_meta(self, paste_id, meta):
        await self.push_paste_all(paste_id, meta=meta)

    async def get_paste_meta(self, paste_id):
        cached = await self._conn.get(f"{paste_id}__meta")
        if cached:
            return PasteMeta.parse_raw(cached)

    async def get_paste_rendered(self, paste_id):
        cached = await self._conn.get(f"{paste_id}__html")
        if cached:
            return cached.decode()

    async def get_paste_raw(self, paste_id):
        return await self._conn.get(f"{paste_id}__raw")
