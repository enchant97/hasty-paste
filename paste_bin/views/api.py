from datetime import datetime

from quart import Blueprint, abort, send_file
from quart_schema import validate_request, validate_response

from .. import helpers
from ..config import get_settings

blueprint = Blueprint("api", __name__, url_prefix="/api")


@blueprint.post("/pastes")
@validate_request(helpers.PasteMetaCreate)
@validate_response(helpers.PasteMeta)
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

    return paste_meta


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

    _, _, response = await helpers.try_get_paste_with_content_response(
        root_path,
        paste_id,
    )

    return response
