import logging

from quart import Quart, g
from quart_schema import QuartSchema
from web_health_checker.contrib import quart as health_check

from . import __version__
from .cache import InternalCache, init_cache
from .config import get_settings
from .views import api, extra_static, frontend

logger = logging.getLogger("paste_bin")
app_version = ".".join(__version__.split(".")[0:2])
app = Quart(__name__)
quart_schema = QuartSchema(
    openapi_path="/api/openapi.json",
    swagger_ui_path="/api/docs",
    redoc_ui_path="/api/redocs",
    title="Hasty Paste",
    version=app_version,
)


def _reset_app():
    """
    reset the internals for use only when running unit tests
    """
    global app
    app = Quart(__name__)
    get_settings.cache_clear()


def create_app():
    settings = get_settings()

    logging.basicConfig()
    logger.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    print(
        "IMPORTANT NOTICE for users before V1.5: Paste id's with symbol" +
        " characters are being deprecated and will be removed in the future, " +
        "please use the \"Clone & Edit\" button to resave under new id (or just delete them)")

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    if not settings.BRANDING.HIDE_VERSION:
        app.config["__version__"] = app_version
    else:
        quart_schema.version = ""

    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_BODY_SIZE
    app.config["BRANDING"] = settings.BRANDING

    app.register_blueprint(frontend.blueprint)
    app.register_blueprint(health_check.blueprint, url_prefix="/api")
    app.register_blueprint(api.blueprint)
    app.register_blueprint(extra_static.blueprint)

    quart_schema.init_app(app)

    init_cache(InternalCache(4))

    return app
