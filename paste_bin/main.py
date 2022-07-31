import logging

from quart import Quart
from quart_schema import QuartSchema
from web_health_checker.contrib import quart as health_check

from . import __version__, views
from .config import get_settings

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

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_BODY_SIZE
    app.config["__version__"] = app_version

    app.register_blueprint(views.front_end)
    app.register_blueprint(health_check.blueprint, url_prefix="/api")
    app.register_blueprint(views.api)

    quart_schema.init_app(app)

    return app
