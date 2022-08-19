from datetime import datetime, timedelta

from quart import (Blueprint, abort, make_response, redirect, render_template,
                   request, send_file, url_for)
from quart_schema import hide_route, validate_request, validate_response

from . import helpers
from .config import get_settings

front_end = Blueprint("front_end", __name__)
api = Blueprint("api", __name__, url_prefix="/api")


@front_end.get("/")
@hide_route
async def get_index():
    if get_settings().NEW_AT_INDEX:
        return await get_new_paste()
    return await render_template("index.jinja")


@front_end.get("/about")
@hide_route
async def get_about():
    return await render_template("about.jinja")


@front_end.get("/favicon.ico")
@hide_route
async def get_favicon():
    return redirect(url_for("static", filename="icon.svg"), 301)


@front_end.get("/new")
@hide_route
async def get_new_paste():
    settings = get_settings()
    default_expires_at = None
    root_path = get_settings().PASTE_ROOT
    content = ""

    if settings.DEFAULT_EXPIRE_TIME:
        default_expires_at = datetime.now()
        default_expires_at += timedelta(
            minutes=settings.DEFAULT_EXPIRE_TIME__MINUTES,
            hours=settings.DEFAULT_EXPIRE_TIME__HOURS,
            days=settings.DEFAULT_EXPIRE_TIME__DAYS,
        )
        default_expires_at = default_expires_at.isoformat(timespec="minutes")

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
        show_long_id_checkbox=True if settings.DEFAULT_USE_LONG_ID is None else False,
        content=content,
    )


@front_end.post("/new")
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
    long_id = True if get_settings().DEFAULT_USE_LONG_ID else False

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


@front_end.get("/<paste_id>", defaults={"lexer_name": None})
@front_end.get("/<paste_id>.<lexer_name>")
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


@front_end.get("/<paste_id>/raw")
@hide_route
@helpers.handle_paste_exceptions
async def get_raw_paste(paste_id: str):
    root_path = get_settings().PASTE_ROOT

    _, _, response = await helpers.try_get_paste_with_content_response(
        root_path,
        paste_id,
    )

    return response


@api.post("/pastes")
@validate_request(helpers.PasteMetaCreate)
@validate_response(helpers.PasteMeta)
async def post_api_paste_new(data: helpers.PasteMetaCreate):
    """
    Create a new paste
    """
    if data.lexer_name and not helpers.is_valid_lexer_name(data.lexer_name):
        # TODO return a better error response
        abort(400)

    # TODO validate in class instead
    title = data.title
    if title is not None:
        title = title.strip()
        if len(title) > 32:
            abort(400)
        title = None if title == "" else title

    paste_meta = helpers.PasteMeta(
        paste_id=helpers.create_paste_id(data.long_id),
        creation_dt=datetime.utcnow(),
        expire_dt=data.expire_dt,
        lexer_name=data.lexer_name,
        title=title,
    )

    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_meta.paste_id, True)

    await helpers.write_paste(paste_path, paste_meta, data.content.encode())

    return paste_meta


@api.get("/pastes/")
async def get_api_paste_ids():
    """
    Get all paste id's, requires `ENABLE_PUBLIC_LIST` to be True
    """
    if not get_settings().ENABLE_PUBLIC_LIST:
        abort(403)

    root_path = get_settings().PASTE_ROOT

    response = await helpers.list_paste_ids_response(root_path)

    return response


@api.get("/pastes/<paste_id>")
@helpers.handle_paste_exceptions
async def get_api_paste_raw(paste_id: str):
    """
    Get the paste raw file, if one exists
    """
    root_path = get_settings().PASTE_ROOT

    paste_path, _, = await helpers.try_get_paste(root_path, paste_id)

    return await send_file(paste_path)


@api.get("/pastes/<paste_id>/meta")
@validate_response(helpers.PasteMeta)
@helpers.handle_paste_exceptions
async def get_api_paste_meta(paste_id: str):
    """
    Get the paste meta, if one exists
    """
    root_path = get_settings().PASTE_ROOT

    _, paste_meta = await helpers.try_get_paste(root_path, paste_id)

    return paste_meta


@api.get("/pastes/<paste_id>/content")
@helpers.handle_paste_exceptions
async def get_api_paste_content(paste_id: str):
    """
    Get the paste content, if one exists
    """
    root_path = get_settings().PASTE_ROOT

    _, _, response = await helpers.try_get_paste_with_content_response(
        root_path,
        paste_id,
    )

    return response
