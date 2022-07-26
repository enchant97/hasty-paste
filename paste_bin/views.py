from datetime import datetime

from quart import (Blueprint, abort, make_response, redirect, render_template,
                   request, url_for)

from . import helpers
from .config import get_settings

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
    form = await request.form

    paste_content = form["paste-content"].replace("\r\n", "\n")
    expires_at = form.get("expires-at", None, helpers.get_form_datetime)
    long_id = form.get("long-id", False, bool)

    paste_meta = helpers.PasteMeta(
        paste_id=helpers.create_paste_id(long_id),
        creation_dt=datetime.utcnow(),
        expire_dt=expires_at,
    )

    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_meta.paste_id, True)

    await helpers.write_paste(paste_path, paste_meta, paste_content.encode())

    return redirect(url_for(".get_view_paste", paste_id=paste_meta.paste_id))


@front_end.get("/<paste_id>")
async def get_view_paste(paste_id: str):
    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_id)

    if not paste_path.is_file():
        abort(404)

    paste_meta = await helpers.read_paste_meta(paste_path)

    if paste_meta.is_expired:
        abort(404)

    content = helpers.read_paste_content(paste_path)

    return await render_template(
        "view.jinja",
        paste_content=content,
    )


@front_end.get("/<paste_id>/raw")
async def get_raw_paste(paste_id: str):
    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_id)

    if not paste_path.is_file():
        abort(404)

    paste_meta = await helpers.read_paste_meta(paste_path)

    if paste_meta.is_expired:
        abort(404)

    content = helpers.read_paste_content(paste_path)

    response = await make_response(content)

    return response
