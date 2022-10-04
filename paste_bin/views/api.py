import logging
from datetime import datetime

from async_timeout import timeout
from quart import (Blueprint, abort, current_app, make_response, request,
                   send_file)
from quart.wrappers import Body
from quart_schema import validate_request, validate_response

from .. import helpers
from ..cache import get_cache
from ..config import get_settings

blueprint = Blueprint("api", __name__, url_prefix="/api")

logger = logging.getLogger("paste_bin")


@blueprint.post("/pastes")
@validate_request(helpers.PasteMetaCreate)
@validate_response(helpers.PasteMeta, status_code=201)
async def post_api_paste_new(data: helpers.PasteMetaCreate):
    """
    Create a new paste
    """
    paste_id = helpers.create_paste_id(data.long_id)
    title = None if data.title == "" else data.title
    creation_dt = datetime.utcnow()

    paste_meta = helpers.PasteMeta(
        paste_id=paste_id,
        creation_dt=creation_dt,
        expire_dt=data.expire_dt,
        lexer_name=data.lexer_name,
        title=title,
    )

    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_meta.paste_id, True)

    await helpers.write_paste(paste_path, paste_meta, data.content.encode())

    return paste_meta, 201


@blueprint.post("/pastes/simple")
async def post_api_paste_new_simple():
    """
    Create a new paste without any fancy features,
    could be used easily with curl by a user.

    Just send the paste content in the request body,
    after paste creation the paste id will be returned in the response body.
    """
    use_long_id = get_settings().UI_DEFAULT.USE_LONG_ID is not None or False
    expiry_settings = get_settings().UI_DEFAULT.EXPIRE_TIME
    paste_id = helpers.create_paste_id(use_long_id)
    creation_dt = datetime.utcnow()

    paste_meta = helpers.PasteMeta(
        paste_id=paste_id,
        creation_dt=creation_dt,
        expire_dt=helpers.make_default_expires_at(expiry_settings),
    )

    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_meta.paste_id, True)

    body: Body = request.body
    # NOTE timeout required as directly using body is not protected by Quart
    async with timeout(current_app.config["BODY_TIMEOUT"]):
        await helpers.write_paste(paste_path, paste_meta, body)

    return paste_meta.paste_id, 201


@blueprint.get("/pastes/")
async def get_api_paste_ids():
    """
    Get all paste id's, requires `ENABLE_PUBLIC_LIST` to be True
    """
    if not get_settings().ENABLE_PUBLIC_LIST:
        abort(403)

    root_path = get_settings().PASTE_ROOT

    response = await helpers.list_paste_ids_response(root_path)

    return response


@blueprint.get("/pastes/<paste_id>")
@helpers.handle_paste_exceptions
async def get_api_paste_raw(paste_id: str):
    """
    Get the paste raw file, if one exists
    """
    root_path = get_settings().PASTE_ROOT

    paste_path, _, = await helpers.try_get_paste(root_path, paste_id)

    return await send_file(paste_path)


@blueprint.get("/pastes/<paste_id>/meta")
@validate_response(helpers.PasteMeta)
@helpers.handle_paste_exceptions
async def get_api_paste_meta(paste_id: str):
    """
    Get the paste meta, if one exists
    """
    root_path = get_settings().PASTE_ROOT

    _, paste_meta = await helpers.try_get_paste(root_path, paste_id)

    return paste_meta


@blueprint.get("/pastes/<paste_id>/content")
@helpers.handle_paste_exceptions
async def get_api_paste_content(paste_id: str):
    """
    Get the paste content, if one exists
    """
    root_path = get_settings().PASTE_ROOT
    paste_path = helpers.create_paste_path(root_path, paste_id)

    paste_meta = None

    try:
        # get the paste, using cache if possible
        if (cached_meta := get_cache().get_paste_meta(paste_id)) is not None:
            logger.debug("accessing paste '%s' meta from cache", paste_id)
            paste_meta = cached_meta
            paste_meta.raise_if_expired()
        else:
            _, paste_meta = await helpers.try_get_paste(root_path, paste_id)

    except helpers.PasteExpiredException as err:
        # register the paste for removal
        current_app.add_background_task(helpers.safe_remove_paste, paste_path, paste_id)
        raise err

    raw_paste = None

    if (cached_raw := get_cache().get_paste_raw(paste_id)) is not None:
        logger.debug("accessing paste '%s' raw content from cache", paste_id)
        raw_paste = cached_raw
    else:
        raw_paste = helpers.read_paste_content(paste_path)
        raw_paste = b"".join([line async for line in raw_paste])
        get_cache().push_paste_all(paste_id, raw=raw_paste)

    response = await make_response(raw_paste)
    response.mimetype = "text/plain"

    return response
