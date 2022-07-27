from quart import Quart
from quart_schema import QuartSchema
from web_health_checker.contrib import quart as health_check

from . import views
from .config import get_settings

app = Quart(__name__)
quart_schema = QuartSchema(
    openapi_path="/api/openapi.json",
    swagger_ui_path="/api/docs",
    redoc_ui_path="/api/redocs",
    title="Paste Bin",
)


def create_app():
    settings = get_settings()

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(views.front_end)
    app.register_blueprint(health_check.blueprint, url_prefix="/api")
    app.register_blueprint(views.api)

    quart_schema.init_app(app)

    return app
