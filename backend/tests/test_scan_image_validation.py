from io import BytesIO

import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.services.image_validation import ImageValidationError, validate_image_upload


def make_image_upload(image_format: str, content_type: str) -> UploadFile:
    content = BytesIO()
    Image.new("RGB", (16, 16), color="green").save(content, format=image_format)
    content.seek(0)
    return UploadFile(
        file=content,
        filename=f"waste.{image_format.lower()}",
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("image_format", "content_type", "extension"),
    [
        ("JPEG", "image/jpeg", ".jpg"),
        ("PNG", "image/png", ".png"),
        ("WEBP", "image/webp", ".webp"),
    ],
)
async def test_accepts_supported_image_content(image_format: str, content_type: str, extension: str) -> None:
    result = await validate_image_upload(make_image_upload(image_format, content_type), max_bytes=1024 * 1024)

    assert result.content_type == content_type
    assert result.extension == extension
    assert result.content


@pytest.mark.asyncio
async def test_rejects_mime_type_that_does_not_match_content() -> None:
    upload = make_image_upload("PNG", "image/jpeg")

    with pytest.raises(ImageValidationError, match="MIME type") as captured:
        await validate_image_upload(upload, max_bytes=1024 * 1024)

    assert captured.value.code == "UNSUPPORTED_IMAGE"


@pytest.mark.asyncio
async def test_rejects_oversized_image_before_decoding() -> None:
    upload = UploadFile(
        file=BytesIO(b"x" * 11),
        filename="large.jpg",
        headers=Headers({"content-type": "image/jpeg"}),
    )

    with pytest.raises(ImageValidationError) as captured:
        await validate_image_upload(upload, max_bytes=10)

    assert captured.value.code == "IMAGE_TOO_LARGE"
