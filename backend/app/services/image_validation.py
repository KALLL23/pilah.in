"""Image upload validation shared by image-backed features."""

from dataclasses import dataclass
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ValidatedImage:
    content: bytes
    content_type: str
    extension: str


async def validate_image_upload(upload: UploadFile, max_bytes: int) -> ValidatedImage:
    if upload.content_type not in {item[0] for item in ALLOWED_IMAGE_FORMATS.values()}:
        raise ImageValidationError("UNSUPPORTED_IMAGE", "Format gambar harus JPEG, PNG, atau WEBP.")

    content = await upload.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ImageValidationError("IMAGE_TOO_LARGE", "Ukuran gambar melebihi batas 8 MB.")
    if not content:
        raise ImageValidationError("UNSUPPORTED_IMAGE", "File gambar kosong atau tidak valid.")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageValidationError("UNSUPPORTED_IMAGE", "Isi file bukan gambar yang valid.") from error

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ImageValidationError("UNSUPPORTED_IMAGE", "Format gambar harus JPEG, PNG, atau WEBP.")
    detected_content_type, extension = ALLOWED_IMAGE_FORMATS[image_format]
    if upload.content_type != detected_content_type:
        raise ImageValidationError("UNSUPPORTED_IMAGE", "MIME type tidak sesuai dengan isi gambar.")

    return ValidatedImage(content=content, content_type=detected_content_type, extension=extension)
