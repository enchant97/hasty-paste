import logging

from async_timeout import timeout
from quart import Blueprint, abort, current_app, make_response, request
from quart.wrappers import Body
from quart_schema import tag, validate_request, validate_response

from ..config import get_settings
from ..core import helpers
from ..core.models import PasteApiCreate, PasteMeta, PasteMetaToCreate
from ..core.paste_handler import get_handler

blueprint = Blueprint("api", __name__, url_prefix="/api")

logger = logging.getLogger("paste_bin")


@blueprint.post("/pastes")
@tag(("paste",))
@validate_request(PasteApiCreate)
@validate_response(PasteMeta, status_code=201)
async def post_api_paste_new(data: PasteApiCreate):
    """
    Create a new paste, expected timezone is UTC
    """
    title = None if data.title == "" else data.title

    paste_handler = get_handler()

    paste_id = await paste_handler.create_paste(
        get_settings().USE_LONG_ID,
        data.content.encode(),
        PasteMetaToCreate(
            expire_dt=data.expire_dt,
            lexer_name=data.lexer_name,
            title=title,
        ),
    )

    paste_meta = await paste_handler.get_paste_meta(paste_id)

    if paste_meta is None:
        abort(500)

    return paste_meta, 201


@blueprint.post("/pastes/simple")
@tag(("paste",))
async def post_api_paste_new_simple():
    """
    Create a new paste without any fancy features,
    could be used easily with curl by a user.

    Just send the paste content in the request body,
    after paste creation the paste id will be returned in the response body.
    """
    expiry_settings = get_settings().UI_DEFAULT.EXPIRE_TIME
    expires_at = helpers.make_default_expires_at(expiry_settings)

    paste_handler = get_handler()

    body: Body = request.body
    # NOTE timeout required as directly using body is not protected by Quart
    async with timeout(current_app.config["BODY_TIMEOUT"]):
        paste_id = await paste_handler.create_paste(
            get_settings().USE_LONG_ID,
            body,
            PasteMetaToCreate(
                expire_dt=expires_at,
            ),
        )

    return paste_id, 201


@blueprint.get("/pastes/")
@tag(("paste",))
async def get_api_paste_ids():
    """
    Get all paste id's, requires `ENABLE_PUBLIC_LIST` to be True
    """
    if not get_settings().ENABLE_PUBLIC_LIST:
        abort(403)

    paste_handler = get_handler()

    response = await make_response(paste_handler.get_all_paste_ids_as_csv())
    response.mimetype = "text/csv"

    return response


@blueprint.get("/pastes/<id:paste_id>")
@tag(("paste",))
@helpers.handle_known_exceptions
async def get_api_paste_raw(paste_id: str):
    """
    Get the paste raw content, if one exists
    """
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


@blueprint.get("/pastes/<id:paste_id>/meta")
@tag(("paste",))
@validate_response(PasteMeta)
@helpers.handle_known_exceptions
async def get_api_paste_meta(paste_id: str):
    """
    Get the paste meta, if one exists
    """
    paste_handler = get_handler()

    paste_meta = await paste_handler.get_paste_meta(paste_id)

    if paste_meta is None:
        abort(404)
    if paste_meta.is_expired:
        await paste_handler.remove_paste(paste_id)
        abort(404)

    return paste_meta
