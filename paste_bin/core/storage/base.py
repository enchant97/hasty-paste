from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ... import helpers


class BaseStorage(ABC):
    """
    The base paste storage class that all storage types should inherit from
    """
    @abstractmethod
    def __init__(self, **kw):
        ...

    @abstractmethod
    async def write_paste(
            self,
            paste_id: str,
            raw: AsyncGenerator[bytes, None] | bytes,
            meta: helpers.PasteMeta):
        ...

    @abstractmethod
    async def read_paste_meta(self, paste_id: str) -> helpers.PasteMeta | None:
        ...

    @abstractmethod
    async def read_paste_raw(self, paste_id: str) -> bytes | None:
        ...

    @abstractmethod
    async def read_all_paste_ids(self) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    async def delete_paste(self, paste_id: str):
        ...
