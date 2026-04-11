"""MinIO (S3-compatible) client for the data lake.

Usage:
    from data_platform.io.minio_client import MinIOClient

    client = MinIOClient()
    client.upload_dataframe(df, "bronze", "crypto/prices/2024-01.parquet")
    df = client.read_parquet("bronze", "crypto/prices/2024-01.parquet")
"""

from __future__ import annotations

import io
import logging
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from minio import Minio
from minio.error import S3Error

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class MinIOClient:
    """Thin wrapper around the MinIO Python SDK for data lake operations."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
    ) -> None:
        self._endpoint = endpoint or self._get_env("MINIO_ENDPOINT", "localhost:9000")
        self._access_key = access_key or self._get_env("MINIO_ACCESS_KEY", "minioadmin")
        self._secret_key = secret_key or self._get_env("MINIO_SECRET_KEY", "minioadmin")
        self._client = Minio(
            self._endpoint,
            access_key=self._access_key,
            secret_key=self._secret_key,
            secure=secure,
        )

    # ── Bucket operations ─────────────────────────────────────────────────

    def ensure_bucket(self, bucket: str) -> None:
        """Create bucket if it doesn't exist."""
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
            logger.info("Created bucket: %s", bucket)

    def list_buckets(self) -> list[str]:
        return [b.name for b in self._client.list_buckets()]

    # ── Upload ────────────────────────────────────────────────────────────

    def upload_bytes(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload raw bytes to MinIO."""
        self.ensure_bucket(bucket)
        buf = io.BytesIO(data)
        self._client.put_object(bucket, key, buf, length=len(data), content_type=content_type)
        logger.info("Uploaded %s/%s (%d bytes)", bucket, key, len(data))

    def upload_json(self, bucket: str, key: str, data: str) -> None:
        """Upload JSON string."""
        self.upload_bytes(bucket, key, data.encode("utf-8"), content_type="application/json")

    def upload_dataframe(self, df: pd.DataFrame, bucket: str, key: str, fmt: str = "parquet") -> None:
        """Upload a pandas DataFrame as Parquet or CSV."""
        buf = io.BytesIO()
        if fmt == "parquet":
            df.to_parquet(buf, index=False, engine="pyarrow")
            content_type = "application/octet-stream"
        elif fmt == "csv":
            df.to_csv(buf, index=False)
            content_type = "text/csv"
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        raw = buf.getvalue()
        self.upload_bytes(bucket, key, raw, content_type=content_type)

    # ── Download ──────────────────────────────────────────────────────────

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download raw bytes from MinIO."""
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def read_parquet(self, bucket: str, key: str) -> pd.DataFrame:
        """Read a Parquet file from MinIO into a DataFrame."""
        import pandas as _pd

        data = self.download_bytes(bucket, key)
        return _pd.read_parquet(io.BytesIO(data), engine="pyarrow")

    def read_json(self, bucket: str, key: str) -> str:
        """Read a JSON file from MinIO."""
        return self.download_bytes(bucket, key).decode("utf-8")

    # ── List / Delete ─────────────────────────────────────────────────────

    def list_objects(self, bucket: str, prefix: str = "", recursive: bool = True) -> list[str]:
        """List object keys in a bucket."""
        objects = self._client.list_objects(bucket, prefix=prefix, recursive=recursive)
        return [obj.object_name for obj in objects]

    def delete_object(self, bucket: str, key: str) -> None:
        self._client.remove_object(bucket, key)
        logger.info("Deleted %s/%s", bucket, key)

    # ── Data Lake helpers ─────────────────────────────────────────────────

    def write_to_layer(
        self,
        df: pd.DataFrame,
        layer: str,
        domain: str,
        partition_key: str,
        fmt: str = "parquet",
    ) -> str:
        """Write DataFrame to the data lake with standard path convention.

        Path: {layer}/{domain}/{partition_key}.{fmt}
        Example: bronze/crypto/prices/2024-01.parquet
        """
        key = str(PurePosixPath(domain) / f"{partition_key}.{fmt}")
        self.upload_dataframe(df, layer, key, fmt=fmt)
        return f"{layer}/{key}"

    def read_from_layer(self, layer: str, domain: str, partition_key: str) -> pd.DataFrame:
        """Read a partition from the data lake."""
        key = str(PurePosixPath(domain) / f"{partition_key}.parquet")
        return self.read_parquet(layer, key)

    # ── Internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_env(key: str, default: str) -> str:
        import os
        return os.environ.get(key, default)
