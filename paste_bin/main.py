from quart import Quart

from . import views
from .config import get_settings

app = Quart(__name__)


def create_app():
    settings = get_settings()

    settings.PASTE_ROOT.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(views.front_end)
    app.register_blueprint(views.api)

    return app
