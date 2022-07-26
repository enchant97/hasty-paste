from quart import Quart
from web_health_checker.contrib import quart as health_check

from . import views
from .config import get_settings

app = Quart(__name__)


def create_app():
    settings = get_settings()

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(views.front_end)
    app.register_blueprint(health_check.blueprint, url_prefix="/api")
    app.register_blueprint(views.api)

    return app
