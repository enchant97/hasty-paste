from datetime import datetime

from quart import Blueprint, abort, redirect, render_template, request, url_for
from quart_schema import hide_route

from .. import helpers
from ..config import get_settings

blueprint = Blueprint("front_end", __name__)


@blueprint.get("/")
@hide_route
async def get_index():
    if get_settings().NEW_AT_INDEX:
        return await get_new_paste()
    return await render_template("index.jinja")


@blueprint.get("/about")
@hide_route
async def get_about():
    return await render_template("about.jinja")


@blueprint.get("/favicon.ico")
@hide_route
async def get_favicon():
    return redirect(url_for("static", filename="icon.svg"), 301)


@blueprint.get("/new")
@hide_route
async def get_new_paste():
    default_settings = get_settings().UI_DEFAULT
    default_expires_at = None
    root_path = get_settings().PASTE_ROOT
    content = ""

    if (expiry := helpers.make_default_expires_at(default_settings)) is not None:
        default_expires_at = expiry.isoformat(timespec="minutes")

    # allow paste to be cloned for editing as new paste
    if (paste_id := request.args.get("clone_from")) is not None:
        try:
            paste_path, _ = await helpers.try_get_paste(root_path, paste_id)
            content = helpers.read_paste_content(paste_path)
            content = "".join([line.decode() async for line in content])
        except (helpers.PasteException, helpers.PasteMetaException):
            # skip clone, if paste errored failed
            pass

    return await render_template(
        "new.jinja",
        default_expires_at=default_expires_at,
        get_highlighter_names=helpers.get_highlighter_names,
        show_long_id_checkbox=True if default_settings.USE_LONG_ID is None else False,
        content=content,
    )


@blueprint.post("/new")
@hide_route
async def post_new_paste():
    form = await request.form

    paste_content = form["paste-content"].replace("\r\n", "\n")
    expires_at = form.get("expires-at", None, helpers.get_form_datetime)
    long_id = form.get("long-id", False, bool)
    lexer_name = form.get("highlighter-name", None)
    title = form.get("title", "", str).strip()
    if len(title) > 32:
        abort(400)
    title = None if title == "" else title

    if lexer_name == "":
        lexer_name = None

    if lexer_name and not helpers.is_valid_lexer_name(lexer_name):
        abort(400)

    # use default long id if enabled
    long_id = True if get_settings().UI_DEFAULT.USE_LONG_ID else False

    paste_meta = helpers.PasteMeta(
        paste_id=helpers.create_paste_id(long_id),
        creation_dt=datetime.utcnow(),
        expire_dt=expires_at,
        lexer_name=lexer_name,
        title=title,
    )

    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_meta.paste_id, True)

    await helpers.write_paste(paste_path, paste_meta, paste_content.encode())

    return redirect(url_for(".get_view_paste", paste_id=paste_meta.paste_id))


@blueprint.get("/<paste_id>", defaults={"lexer_name": None})
@blueprint.get("/<paste_id>.<lexer_name>")
@hide_route
@helpers.handle_paste_exceptions
async def get_view_paste(paste_id: str, lexer_name: str | None):
    root_path = get_settings().PASTE_ROOT

    paste_path, paste_meta = await helpers.try_get_paste(root_path, paste_id)

    content = helpers.read_paste_content(paste_path)

    content = "".join([line.decode() async for line in content])

    if not lexer_name:
        lexer_name = paste_meta.lexer_name or "text"

    content = await helpers.highlight_content_async_wrapped(content, lexer_name)

    return await render_template(
        "view.jinja",
        paste_content=content,
        meta=paste_meta,
    )


@blueprint.get("/<paste_id>/raw")
@hide_route
@helpers.handle_paste_exceptions
async def get_raw_paste(paste_id: str):
    root_path = get_settings().PASTE_ROOT

    _, _, response = await helpers.try_get_paste_with_content_response(
        root_path,
        paste_id,
    )

    return response
