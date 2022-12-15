import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from collections.abc import AsyncGenerator
from io import BytesIO
import base64
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = None

from quart import Quart

from .base import BaseStorage
from .exceptions import StorageReadException, StorageWriteException
from ..models import PasteMeta
from ..helpers import OptionalRequirementMissing
from ...config import S3StorageSettings

logger = logging.getLogger("paste_bin")


def paste_meta_to_s3(meta: PasteMeta) -> dict:
    s3_meta = {
        "version": str(meta.version),
        "creation_dt": meta.creation_dt.isoformat(),
    }
    if meta.expire_dt:
        s3_meta["expire_dt"] = meta.expire_dt.isoformat()
    if meta.lexer_name:
        s3_meta["lexer_name"] = meta.lexer_name
    if meta.title:
        s3_meta["title"] = base64.b64encode(meta.title.encode()).decode()
    return s3_meta


def s3_into_paste_meta(paste_id: str, s3_meta: dict) -> PasteMeta:
    meta = {
        "version": int(s3_meta["version"]),
        "paste_id": paste_id,
        "creation_dt": datetime.fromisoformat(s3_meta["creation_dt"]),
        "lexer_name": s3_meta.get("lexer_name"),
    }
    if expires_at := s3_meta.get("expire_dt"):
        meta["expire_dt"] = datetime.fromisoformat(expires_at)
    if title := s3_meta.get("title"):
        meta["title"] = base64.b64decode(title).decode()
    return PasteMeta(**meta)


class S3Storage(BaseStorage):
    _executor_pool: ThreadPoolExecutor
    def __init__(self, app: Quart, s3_settings: S3StorageSettings):

        if boto3 is None:
            raise OptionalRequirementMissing(
                "'boto3' requirement must be installed for s3 storage"
            )

        @app.while_serving
        async def handle_lifespan():
            self._executor_pool = ThreadPoolExecutor(thread_name_prefix="s3")
            self._client = boto3.client("s3", **s3_settings.to_boto3_config())
            self._client_upload_fileobj = self._aio_decorator(self._client.upload_fileobj)
            self._client_head_object = self._aio_decorator(self._client.head_object)
            self._client_download_fileobj = self._aio_decorator(self._client.download_fileobj)
            self._client_delete_object = self._aio_decorator(self._client.delete_object)
            self._client_list_objects_v2 = self._aio_decorator(self._client.list_objects_v2)
            self._bucket_name = s3_settings.BUCKET_NAME
            # TODO check if bucket exists, create if not
            yield
            self._executor_pool.shutdown(wait=True)

    def _aio_decorator(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            bound_func = partial(func, *args, **kwargs)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._executor_pool, bound_func)
        return wrapper

    async def write_paste(
            self,
            paste_id: str,
            raw: AsyncGenerator[bytes, None] | bytes,
            meta: PasteMeta):
        try:
            with BytesIO() as raw_bytes:
                if isinstance(raw, bytes):
                    raw_bytes.write(raw)
                else:
                    async for chunk in raw:
                        raw_bytes.write(chunk)
                await self._client_upload_fileobj(
                    BytesIO(raw), self._bucket_name, paste_id,
                    ExtraArgs={"Metadata": paste_meta_to_s3(meta)},
                )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            raise StorageWriteException(
                f"failed to write paste data for '{paste_id}', code '{code}'") from err

    async def read_paste_meta(self, paste_id: str) -> PasteMeta | None:
        try:
            obj = await self._client_head_object(Bucket=self._bucket_name, Key=paste_id)
            return s3_into_paste_meta(paste_id, obj["Metadata"])
        except ClientError as err:
            code = err.response["Error"]["Code"]
            match code:
                case "404":
                    logger.debug("paste id of '%s' not found", paste_id)
                case _:
                    raise StorageReadException(
                        f"failed to read paste meta for '{paste_id}', code '{code}'") from err

    async def read_paste_raw(self, paste_id: str) -> bytes | None:
        try:
            with BytesIO() as raw_bytes:
                await self._client_download_fileobj(self._bucket_name, paste_id, raw_bytes)
                raw_bytes.seek(0)
                return raw_bytes.read()
        except ClientError as err:
            code = err.response["Error"]["Code"]
            match code:
                case "404":
                    logger.debug("paste id of '%s' not found", paste_id)
                case _:
                    raise StorageReadException(
                        f"failed to read paste raw for '{paste_id}', code '{code}'") from err


    async def read_all_paste_ids(self) -> AsyncGenerator[str, None]:
        # FIXME this is limited to 1000 entries? according to aws docs
        try:
            for obj in (await self._client_list_objects_v2(Bucket=self._bucket_name))["Contents"]:
                yield obj["Key"]
        except ClientError as err:
            code = err.response["Error"]["Code"]
            raise StorageReadException(
                f"failed to write paste data for '{paste_id}', code '{code}'") from err

    async def delete_paste(self, paste_id: str):
        try:
            await self._client_delete_object(Bucket=self._bucket_name, Key=paste_id)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            match code:
                case "404":
                    pass
                case _:
                    raise StorageWriteException(
                        f"failed to delete paste '{paste_id}', code '{code}'") from err
