from quart import Blueprint, abort, send_file

from ..config import get_settings

blueprint = Blueprint("extra_static", __name__, url_prefix="/static")


@blueprint.get("/brand-icon")
async def get_brand_icon():
    path = get_settings().BRANDING.ICON
    if not path:
        abort(404)
    return await send_file(path)


@blueprint.get("/brand-favicon")
async def get_brand_favicon():
    path = get_settings().BRANDING.FAVICON
    if not path:
        abort(404)
    return await send_file(path)
