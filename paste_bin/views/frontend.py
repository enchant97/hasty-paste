import logging
from datetime import datetime

from quart import (Blueprint, abort, current_app, make_response, redirect,
                   render_template, request, url_for)
from quart_schema import hide

from .. import helpers
from ..cache import get_cache
from ..config import get_settings

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
    root_path = get_settings().PASTE_ROOT
    content = ""

    if (expiry := helpers.make_default_expires_at(default_settings.EXPIRE_TIME)) is not None:
        default_expires_at = expiry.isoformat(timespec="minutes")

    # allow paste to be cloned for editing as new paste
    if (paste_id := request.args.get("clone_from")) is not None:
        paste_path = helpers.create_paste_path(root_path, paste_id)
        try:
            # get the paste, using cache if possible
            if (cached_meta := await get_cache().get_paste_meta(paste_id)) is not None:
                logger.debug("accessing paste '%s' meta from cache", paste_id)
                paste_meta = cached_meta
                paste_meta.raise_if_expired()
            else:
                paste_meta = await helpers.try_get_paste(paste_path, paste_id)
                await get_cache().push_paste_meta(paste_id, paste_meta)

            # get raw paste content, using cache if possible
            raw_paste = None
            if (cached_raw := await get_cache().get_paste_raw(paste_id)) is not None:
                logger.debug("accessing paste '%s' raw content from cache", paste_id)
                raw_paste = cached_raw
            else:
                raw_paste = helpers.read_paste_content(paste_path)
                raw_paste = b"".join([line async for line in raw_paste])
                await get_cache().push_paste_all(paste_id, raw=raw_paste)
            content = raw_paste.decode()
        except helpers.PasteExpiredException:
            # register the paste for removal
            current_app.add_background_task(helpers.safe_remove_paste, paste_path, paste_id)
            pass
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
@hide
async def post_new_paste():
    form = await request.form

    paste_content = (form["paste-content"].replace("\r\n", "\n")).encode()
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

    await helpers.write_paste(paste_path, paste_meta, paste_content)

    await get_cache().push_paste_all(paste_meta.paste_id, meta=paste_meta, raw=paste_content)

    return redirect(url_for(".get_view_paste", paste_id=paste_meta.paste_id))


@blueprint.get("/<paste_id>", defaults={"override_lexer": None})
@blueprint.get("/<paste_id>.<override_lexer>")
@hide
@helpers.handle_paste_exceptions
async def get_view_paste(paste_id: str, override_lexer: str | None):
    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_id)

    paste_meta = None

    try:
        # get the paste, using cache if possible
        if (cached_meta := await get_cache().get_paste_meta(paste_id)) is not None:
            logger.debug("accessing paste '%s' meta from cache", paste_id)
            paste_meta = cached_meta
            paste_meta.raise_if_expired()
        else:
            paste_meta = await helpers.try_get_paste(paste_path, paste_id)
            await get_cache().push_paste_meta(paste_id, paste_meta)

    except helpers.PasteExpiredException as err:
        # register the paste for removal
        current_app.add_background_task(helpers.safe_remove_paste, paste_path, paste_id)
        raise err

    raw_paste = None
    rendered_paste = None

    # HACK 'lexer_name is None', this should be fixed by caching overhaul in 1.7
    if override_lexer is None and (cached_rendered := await get_cache().get_paste_rendered(paste_id)) is not None:
        logger.debug("accessing paste '%s' rendered content from cache", paste_id)
        rendered_paste = cached_rendered
    else:
        if (cached_raw := await get_cache().get_paste_raw(paste_id)) is not None:
            logger.debug("accessing paste '%s' raw content from cache", paste_id)
            raw_paste = cached_raw
        else:
            raw_paste = helpers.read_paste_content(paste_path)
            raw_paste = b"".join([line async for line in raw_paste])
            await get_cache().push_paste_all(paste_id, raw=raw_paste)

        lexer_name = override_lexer or paste_meta.lexer_name or "text"

        rendered_paste = await helpers.highlight_content_async_wrapped(
            raw_paste.decode(),
            lexer_name
        )

        # HACK override lexer content cannot be cached, should be fixed in 1.7
        if override_lexer is None:
            await get_cache().push_paste_all(paste_id, html=rendered_paste)

    return await render_template(
        "view.jinja",
        paste_content=rendered_paste,
        meta=paste_meta,
    )


@blueprint.get("/<paste_id>/raw")
@hide
@helpers.handle_paste_exceptions
async def get_raw_paste(paste_id: str):
    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_id)

    paste_meta = None

    try:
        # get the paste, using cache if possible
        if (cached_meta := await get_cache().get_paste_meta(paste_id)) is not None:
            logger.debug("accessing paste '%s' meta from cache", paste_id)
            paste_meta = cached_meta
            paste_meta.raise_if_expired()
        else:
            paste_meta = await helpers.try_get_paste(paste_path, paste_id)
            await get_cache().push_paste_meta(paste_id, paste_meta)

    except helpers.PasteExpiredException as err:
        # register the paste for removal
        current_app.add_background_task(helpers.safe_remove_paste, paste_path, paste_id)
        raise err

    raw_paste = None

    if (cached_raw := await get_cache().get_paste_raw(paste_id)) is not None:
        logger.debug("accessing paste '%s' raw content from cache", paste_id)
        raw_paste = cached_raw
    else:
        raw_paste = helpers.read_paste_content(paste_path)
        raw_paste = b"".join([line async for line in raw_paste])
        await get_cache().push_paste_all(paste_id, raw=raw_paste)

    response = await make_response(raw_paste)
    response.mimetype = "text/plain"

    return response
