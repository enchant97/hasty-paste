from quart import Quart

app = Quart(__name__)


def create_app():
    return app
