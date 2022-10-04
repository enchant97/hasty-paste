from quart import Blueprint, abort, send_file
from quart_schema import hide

from ..config import get_settings

blueprint = Blueprint("extra_static", __name__, url_prefix="/static")


@blueprint.get("/brand.css")
@hide
async def get_brand_css():
    path = get_settings().BRANDING.CSS_FILE
    if not path:
        abort(404)
    return await send_file(path)


@blueprint.get("/brand-icon")
@hide
async def get_brand_icon():
    path = get_settings().BRANDING.ICON
    if not path:
        abort(404)
    return await send_file(path)


@blueprint.get("/brand-favicon")
@hide
async def get_brand_favicon():
    path = get_settings().BRANDING.FAVICON
    if not path:
        abort(404)
    return await send_file(path)
