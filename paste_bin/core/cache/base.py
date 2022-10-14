
from abc import ABC, abstractmethod

from ..models import PasteMeta


class BaseCache(ABC):
    """
    The base cache class that all cache types should inherit from
    """
    @abstractmethod
    def __init__(self, **kw):
        ...

    @abstractmethod
    async def push_paste_any(
            self,
            paste_id: str,
            /,
            *,
            meta: PasteMeta | None = None,
            html: str | None = None,
            raw: bytes | None = None):
        """
        create or update parts (or all) of the cached paste
        """
        ...

    @abstractmethod
    async def get_paste_meta(self, paste_id: str) -> PasteMeta:
        """
        Get the cached paste meta, if in cache
        """
        ...

    @abstractmethod
    async def get_paste_rendered(self, paste_id: str) -> str | None:
        """
        Get the cached rendered paste content, if in cache
        """
        ...

    @abstractmethod
    async def get_paste_raw(self, paste_id: str) -> bytes | None:
        """
        Get the cached raw paste content, if in cache
        """
        ...

    @abstractmethod
    async def remove_paste(self, paste_id: str):
        """
        Remove the cached paste, if in cache
        """
        ...
