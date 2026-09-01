"""Private MinIO object storage integration."""

from __future__ import annotations

import asyncio
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, get_settings


class StorageError(Exception):
    pass


class ObjectStorage:
    def __init__(
        self,
        settings: Settings,
        client: BaseClient | None = None,
        signing_client: BaseClient | None = None,
    ) -> None:
        self.bucket = settings.minio_bucket
        self.presigned_expiry = settings.presigned_url_expiry_seconds
        self.client = client or self._build_client(settings, settings.minio_url)
        self.signing_client = signing_client or client or self._build_client(settings, settings.minio_public_url)

    @staticmethod
    def _build_client(settings: Settings, endpoint_url: str) -> BaseClient:
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.minio_access_key.get_secret_value(),
            aws_secret_access_key=settings.minio_secret_key.get_secret_value(),
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            region_name="us-east-1",
        )

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Image upload failed") from error

    async def check_ready(self) -> None:
        """Verify that the configured private bucket is reachable."""
        try:
            await asyncio.to_thread(self.client.head_bucket, Bucket=self.bucket)
        except (BotoCoreError, ClientError) as error:
            raise StorageError("MinIO bucket is not ready") from error

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Image cleanup failed") from error

    def presigned_get_url(self, key: str) -> str:
        try:
            return self.signing_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=self.presigned_expiry,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Image URL generation failed") from error

    def download(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Image download failed") from error


@lru_cache
def get_object_storage() -> ObjectStorage:
    return ObjectStorage(get_settings())
