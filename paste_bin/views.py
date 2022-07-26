from quart import Blueprint, render_template

front_end = Blueprint("front_end", __name__)
api = Blueprint("api", __name__, url_prefix="/api")


@front_end.get("/")
async def get_index():
    return await render_template("index.jinja")


@front_end.get("/new")
async def get_new_paste():
    return await render_template("new.jinja")


@front_end.post("/new")
async def post_new_paste():
    pass


@front_end.get("/<paste_id>")
async def get_view_paste(paste_id: str):
    return await render_template("view.jinja")


@front_end.get("/<paste_id>/raw")
async def get_raw_paste(paste_id: str):
    pass
