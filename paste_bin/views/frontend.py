import logging

from quart import (Blueprint, abort, make_response, redirect, render_template,
                   request, url_for)
from quart_schema import hide

from .. import helpers
from ..config import get_settings
from ..core import renderer
from ..core.conversion import (form_field_to_datetime, local_to_utc,
                               utc_to_local)
from ..core.paste_handler import get_handler

blueprint = Blueprint("front_end", __name__)

logger = logging.getLogger("paste_bin")


@blueprint.get("/")
@hide
async def get_index():
    if get_settings().NEW_AT_INDEX:
        return await get_new_paste()
    return await render_template("index.jinja")


@blueprint.get("/about")
@hide
async def get_about():
    return await render_template("about.jinja")


@blueprint.get("/favicon.ico")
@hide
async def get_favicon():
    return redirect(url_for("static", filename="icon.svg"), 301)


@blueprint.get("/new")
@hide
async def get_new_paste():
    default_settings = get_settings().UI_DEFAULT
    default_expires_at = None
    content = ""

    if (expiry := helpers.make_default_expires_at(default_settings.EXPIRE_TIME)) is not None:
        # NOTE ensure client has it in their timezone, not server's
        expiry = utc_to_local(expiry, get_settings().TIME_ZONE)
        default_expires_at = expiry.isoformat(timespec="minutes")

    # allow paste to be cloned for editing as new paste
    if (paste_id := request.args.get("clone_from")) is not None:
        paste_handler = get_handler()
        try:
            if (meta := await paste_handler.get_paste_meta(paste_id)) is not None:
                if meta.is_expired:
                    await paste_handler.remove_paste(paste_id)
                    abort(404)
                if (raw := await paste_handler.get_paste_raw(paste_id)) is not None:
                    content = raw.decode()
        except (helpers.PasteException, helpers.PasteMetaException):
            # skip clone, if paste errored failed
            pass

    return await render_template(
        "new.jinja",
        default_expires_at=default_expires_at,
        get_highlighter_names=renderer.get_highlighter_names,
        show_long_id_checkbox=True if default_settings.USE_LONG_ID is None else False,
        content=content,
    )


@blueprint.post("/new")
@hide
async def post_new_paste():
    form = await request.form

    paste_content = (form["paste-content"].replace("\r\n", "\n")).encode()
    expires_at = form.get("expires-at", None, form_field_to_datetime)
    if expires_at:
        # NOTE ensure client's timezone is converted to server's
        expires_at = local_to_utc(expires_at, get_settings().TIME_ZONE)
    long_id = form.get("long-id", False, bool)
    lexer_name = form.get("highlighter-name", None)
    title = form.get("title", "", str).strip()
    if len(title) > 32:
        abort(400)
    title = None if title == "" else title

    if lexer_name == "":
        lexer_name = None

    if lexer_name and not renderer.is_valid_lexer_name(lexer_name):
        abort(400)

    # use default long id if enabled
    long_id = True if get_settings().UI_DEFAULT.USE_LONG_ID else False

    paste_handler = get_handler()

    paste_id = await paste_handler.create_paste(
        long_id,
        paste_content,
        helpers.PasteMetaToCreate(
            expire_dt=expires_at,
            lexer_name=lexer_name,
            title=title,
        ),
    )

    return redirect(url_for(".get_view_paste", paste_id=paste_id))


@blueprint.get("/<id:paste_id>", defaults={"override_lexer": None})
@blueprint.get("/<id:paste_id>.<override_lexer>")
@hide
@helpers.handle_paste_exceptions
async def get_view_paste(paste_id: str, override_lexer: str | None):
    paste_handler = get_handler()

    paste_meta = await paste_handler.get_paste_meta(paste_id)

    if paste_meta is None:
        abort(404)
    if paste_meta.is_expired:
        await paste_handler.remove_paste(paste_id)
        abort(404)

    rendered_paste = await paste_handler.get_paste_rendered(paste_id, override_lexer)

    if rendered_paste is None:
        abort(500)

    return await render_template(
        "view.jinja",
        paste_content=rendered_paste,
        meta=paste_meta,
    )


@blueprint.get("/<id:paste_id>/raw")
@hide
@helpers.handle_paste_exceptions
async def get_raw_paste(paste_id: str):
    paste_handler = get_handler()

    paste_meta = await paste_handler.get_paste_meta(paste_id)

    if paste_meta is None:
        abort(404)
    if paste_meta.is_expired:
        await paste_handler.remove_paste(paste_id)
        abort(404)

    raw_paste = await paste_handler.get_paste_raw(paste_id)

    if raw_paste is None:
        abort(500)

    response = await make_response(raw_paste)
    response.mimetype = "text/plain"

    return response
