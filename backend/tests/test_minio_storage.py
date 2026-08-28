from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.services.storage import ObjectStorage, StorageError


def make_storage() -> tuple[ObjectStorage, Mock, Mock]:
    internal = Mock()
    signing = Mock()
    storage = ObjectStorage(Settings(), client=internal, signing_client=signing)
    return storage, internal, signing


@pytest.mark.asyncio
async def test_check_ready_uses_private_internal_endpoint_client() -> None:
    storage, internal, signing = make_storage()

    await storage.check_ready()

    internal.head_bucket.assert_called_once_with(Bucket="pilahin")
    signing.head_bucket.assert_not_called()


@pytest.mark.asyncio
async def test_upload_and_delete_use_internal_client() -> None:
    storage, internal, _signing = make_storage()

    await storage.upload("scans/2026/08/image.jpg", b"image", "image/jpeg")
    await storage.delete("scans/2026/08/image.jpg")

    internal.put_object.assert_called_once_with(
        Bucket="pilahin",
        Key="scans/2026/08/image.jpg",
        Body=b"image",
        ContentType="image/jpeg",
    )
    internal.delete_object.assert_called_once_with(
        Bucket="pilahin",
        Key="scans/2026/08/image.jpg",
    )


def test_presigned_url_uses_public_signing_client() -> None:
    storage, internal, signing = make_storage()
    signing.generate_presigned_url.return_value = "http://192.168.1.10:9000/signed"

    url = storage.presigned_get_url("scans/2026/08/image.jpg")

    assert url == "http://192.168.1.10:9000/signed"
    signing.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "pilahin", "Key": "scans/2026/08/image.jpg"},
        ExpiresIn=900,
    )
    internal.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_storage_client_error_is_exposed_as_storage_error() -> None:
    storage, internal, _signing = make_storage()
    internal.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "missing"}},
        "HeadBucket",
    )

    with pytest.raises(StorageError, match="bucket is not ready"):
        await storage.check_ready()
