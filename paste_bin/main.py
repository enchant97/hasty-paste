import logging
import sys

from quart import Quart
from quart_schema import QuartSchema
from web_health_checker.contrib import quart as health_check

from . import __version__
from .config import get_settings
from .core.cache import FakeCache, InternalCache, RedisCache
from .core.helpers import OptionalRequirementMissing, PasteIdConverter
from .core.paste_handler import PasteHandler, init_handler
from .core.storage import DiskStorage
from .views import api, extra_static, frontend

logger = logging.getLogger("paste_bin")
app_version = ".".join(__version__.split(".")[0:2])
app = Quart(__name__)
quart_schema = QuartSchema(
    openapi_path="/api/openapi.json",
    swagger_ui_path="/api/docs",
    redoc_ui_path="/api/redocs",
    info={
        "title": "Hasty Paste",
        "version": app_version,
    },
)


def _reset_app():
    """
    reset the internals for use only when running unit tests
    """
    global app
    app = Quart(__name__)
    get_settings.cache_clear()


def create_app():
    app.url_map.converters["id"] = PasteIdConverter

    settings = get_settings()

    logging.basicConfig()
    logger.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    if not settings.BRANDING.HIDE_VERSION:
        app.config["__version__"] = app_version

    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_BODY_SIZE
    app.config["BRANDING"] = settings.BRANDING

    app.register_blueprint(frontend.blueprint)
    app.register_blueprint(health_check.blueprint, url_prefix="/api")
    app.register_blueprint(api.blueprint)
    app.register_blueprint(extra_static.blueprint)

    quart_schema.init_app(app)

    try:
        # number of cache levels
        cache_levels = 0
        # primary cache, with or without fallback(s)
        cache = None
        if settings.CACHE.ENABLE:
            # possible configurable cache types,
            # last one selected is primary

            if redis_url := settings.CACHE.REDIS_URI:
                cache_levels += 1
                logger.debug("using redis caching feature")
                cache = RedisCache(
                    fallback=cache,
                    app=app,
                    redis_url=redis_url
                )

            if settings.CACHE.INTERNAL_MAX_SIZE > 0:
                cache_levels += 1
                logger.debug("using internal caching feature")
                cache = InternalCache(
                    fallback=cache,
                    max_size=settings.CACHE.INTERNAL_MAX_SIZE,
                )

        if cache is None:
            # no cache was configured, so fallback to fake one
            logger.debug("caching disabled")
            cache = FakeCache()

        logger.debug("configured %s level(s) of caching", cache_levels)

        paste_handler = PasteHandler(
            DiskStorage(settings.PASTE_ROOT),
            cache,
        )

        init_handler(paste_handler)

    except OptionalRequirementMissing as err:
        logger.critical("%s", err.args[0])
        sys.exit(1)

    return app
