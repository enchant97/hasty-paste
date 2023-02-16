import logging
import sys

from quart import Quart, render_template
from quart_schema import QuartSchema
from web_health_checker.contrib import quart as health_check

from . import __version__
from .config import get_settings, StorageTypes
from .core.cache import FakeCache, InternalCache, RedisCache
from .core.helpers import OptionalRequirementMissing, PasteIdConverter
from .core.json import CustomJSONProvider
from .core.paste_handler import PasteHandler, init_handler
from .core.storage import DiskStorage, S3Storage
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


@app.errorhandler(404)
async def get_404(_):
    return await render_template("404.jinja"), 404


def _reset_app():
    """
    reset the internals for use only when running unit tests
    """
    global app
    app = Quart(__name__)
    get_settings.cache_clear()


def create_app():
    app.json = CustomJSONProvider
    app.url_map.converters["id"] = PasteIdConverter

    settings = get_settings()
    # HACK pydantic can't do what I want
    settings.STORAGE.ensure_valid()

    logging.basicConfig()
    logger.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    # NOTE secrets are redacted, these fields should be 'SecretStr' types
    logger.info("Launching with below config:\n%s", settings.json(indent=4))

    if settings.UI_DEFAULT.USE_LONG_ID is None:
        logger.warning(
            "an unset UI_DEFAULT__USE_LONG_ID is deprecated" +
            ", please set to 'true' or 'false'"
        )

    if settings.STORAGE.DISK.PASTE_ROOT:
        settings.STORAGE.DISK.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

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
                    redis_url=redis_url.get_secret_value(),
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

        storage = None

        match settings.STORAGE.TYPE:
            case StorageTypes.DISK:
                logger.debug("using disk storage")
                storage = DiskStorage(settings.STORAGE.DISK.PASTE_ROOT)
            case StorageTypes.S3:
                logger.debug("using S3 storage")
                storage = S3Storage(app, settings.STORAGE.S3)
            case _:
                raise ValueError("unhandled storage type")

        paste_handler = PasteHandler(
            storage,
            cache,
        )

        init_handler(paste_handler)

    except OptionalRequirementMissing as err:
        logger.critical("%s", err.args[0])
        sys.exit(1)

    print(""" _   _   _   ___ _______   __  ___  _   ___ _____ ___
| |_| | /_\ / __|_   _\ \ / / | _ \/_\ / __|_   _| __|
|  _  |/ _ \\\\__ \ | |  \ V /  |  _/ _ \\\\__ \ | | | _|
|_| |_/_/ \_\___/ |_|   |_|   |_|/_/ \_\___/ |_| |___|  V""" + __version__ + "\n")

    return app
