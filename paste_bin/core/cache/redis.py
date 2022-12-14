import asyncio
import logging

from quart import Quart

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ImportError:
    Redis = None

from ..helpers import OptionalRequirementMissing
from ..models import PasteMeta
from .base import BaseCache
from .exceptions import CacheException

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
            # check redis can be reached
            for attempt in range(1, 7):
                try:
                    await self._conn.ping()
                    break
                except RedisError as err:
                    logger.warning("failed to connect to redis, attempt %d of 6", attempt)
                    if attempt >= 6:
                        logger.critical("could not connect to redis")
                        raise CacheException("could not connect to redis") from err
                    await asyncio.sleep(attempt)
            logger.info("connected to redis")
            yield
            logger.info("closing redis connection...")
            await self._conn.close()
            logger.info("closed redis connection")

    async def push_paste_any(
            self,
            paste_id,
            /, *,
            meta=None,
            html=None,
            raw=None,
            update_fallback: bool = True):
        to_cache = {}

        if meta:
            to_cache[f"{paste_id}__meta"] = meta.json()
        if html:
            to_cache[f"{paste_id}__html"] = html
        if raw:
            to_cache[f"{paste_id}__raw"] = raw

        try:
            await self._conn.mset(to_cache)
        except RedisError as err:
            logger.error("failed to connect to redis cache: '%s'", err.args)

        if self._fallback and update_fallback:
            await self._fallback.push_paste_any(paste_id, meta=meta, html=html, raw=raw)

    async def get_paste_meta(self, paste_id):
        cached = None
        try:
            cached = await self._conn.get(f"{paste_id}__meta")
            if cached:
                cached = PasteMeta.parse_raw(cached)
        except RedisError as err:
            logger.error("failed to connect to redis cache: '%s'", err.args)

        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_meta(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, meta=cached, update_fallback=False)
        return cached

    async def get_paste_rendered(self, paste_id):
        cached = None
        try:
            cached = await self._conn.get(f"{paste_id}__html")
            if cached:
                cached = cached.decode()
        except RedisError as err:
            logger.error("failed to connect to redis cache: '%s'", err.args)

        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_rendered(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, html=cached, update_fallback=False)
        return cached

    async def get_paste_raw(self, paste_id):
        cached = None
        try:
            cached = await self._conn.get(f"{paste_id}__raw")
        except RedisError as err:
            logger.error("failed to connect to redis cache: '%s'", err.args)

        if cached is None and self._fallback:
            cached = await self._fallback.get_paste_raw(paste_id)
            if cached is not None:
                await self.push_paste_any(paste_id, raw=cached, update_fallback=False)
        return cached

    async def remove_paste(self, paste_id: str):
        try:
            await self._conn.delete(
                f"{paste_id}__meta",
                f"{paste_id}__html",
                f"{paste_id}__raw",
            )
        except RedisError as err:
            logger.error("failed to connect to redis cache: '%s'", err.args)
