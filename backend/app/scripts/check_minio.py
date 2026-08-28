"""Smoke-test MinIO upload, private access, presigned download, and cleanup."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import httpx

from app.core.config import Settings
from app.services.storage import ObjectStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the pilah.in MinIO setup.")
    parser.add_argument("--endpoint", default="localhost:9000", help="MinIO endpoint reachable by this command")
    parser.add_argument(
        "--public-endpoint",
        default="localhost:9000",
        help="Endpoint embedded in the presigned URL",
    )
    return parser.parse_args()


def load_settings(endpoint: str, public_endpoint: str) -> Settings:
    root_env = Path(__file__).resolve().parents[3] / ".env"
    return Settings(
        _env_file=root_env if root_env.is_file() else None,
        minio_endpoint=endpoint,
        minio_public_endpoint=public_endpoint,
    )


async def check_minio(endpoint: str, public_endpoint: str) -> None:
    settings = load_settings(endpoint, public_endpoint)
    storage = ObjectStorage(settings)
    key = f"smoke-tests/{uuid4()}.txt"
    payload = b"pilah.in minio smoke test"

    await storage.check_ready()
    await storage.upload(key, payload, "text/plain")
    try:
        presigned_url = storage.presigned_get_url(key)
        unsigned_url = f"{settings.minio_public_url}/{quote(settings.minio_bucket)}/{quote(key)}"
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            signed_response = await client.get(presigned_url)
            if signed_response.status_code != 200 or signed_response.content != payload:
                raise RuntimeError(
                    f"Presigned download failed with HTTP {signed_response.status_code}"
                )

            unsigned_response = await client.get(unsigned_url)
            if unsigned_response.status_code not in {401, 403}:
                raise RuntimeError(
                    "Bucket is not private: unsigned object request was not rejected "
                    f"(HTTP {unsigned_response.status_code})"
                )
    finally:
        await storage.delete(key)

    print(f"MinIO ready: bucket={settings.minio_bucket}, public_endpoint={public_endpoint}")
    print("Verified: upload, private bucket, presigned download, and cleanup")


def main() -> None:
    args = parse_args()
    asyncio.run(check_minio(args.endpoint, args.public_endpoint))


if __name__ == "__main__":
    main()
