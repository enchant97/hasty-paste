"""
Handles using optional JSON accelerator (orjson) or just standard json module.
"""

__all__ = [
    "ACCELERATOR_AVAILABLE",
    "dumps", "loads",
    "CustomJSONProvider",
]

from quart.json.provider import JSONProvider

try:
    import orjson as _json
    ACCELERATOR_AVAILABLE = True
except ImportError:
    import json as _json
    ACCELERATOR_AVAILABLE = False


def dumps(v, **kw):
    """
    json dumps, using accelerator if available
    """
    if ACCELERATOR_AVAILABLE:
        return _json.dumps(v).decode()
    return _json.dumps(v, **kw)


def loads(v, **kw):
    """
    json loads, using accelerator if available
    """
    if ACCELERATOR_AVAILABLE:
        return _json.loads(v)
    return _json.loads(v, **kw)


class CustomJSONProvider(JSONProvider):
    def dumps(self, object_, **kwargs) -> str:
        return dumps(object_, **kw)

    def loads(self, object_, **kwargs):
        return loads(object_, **kw)
