from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    app_timezone: str = "Asia/Jakarta"
    database_host: str = "postgres"
    database_port: int = 5432
    database_name: str = "pilahin"
    database_user: str = "pilahin"
    database_password: str = Field(default="pilahin-local-only", min_length=8)
    jwt_secret_key: str = Field(default="pilahin-dev-secret-key-change-in-production", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    jwt_secret: SecretStr | None = None
    access_token_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_days: int = Field(default=30, ge=1, le=365)
    admin_email: str | None = None
    admin_password: SecretStr | None = None
    minio_endpoint: str = "minio:9000"
    minio_public_endpoint: str | None = None
    minio_access_key: SecretStr = SecretStr("pilahin-local")
    minio_secret_key: SecretStr = SecretStr("pilahin-local-secret")
    minio_bucket: str = "pilahin"
    minio_secure: bool = False
    presigned_url_expiry_seconds: int = Field(default=900, ge=60, le=86400)
    classification_model: Path = Path("/models/waste_cls.pt")
    classification_model_version: str = Field(default="PILAH-CLS-v0.1.0", min_length=1, max_length=80)
    classification_image_size: int = Field(default=224, ge=32, le=2048)
    model_confidence_threshold: float = Field(default=0.70, ge=0, le=1)
    max_image_bytes: int = Field(default=8 * 1024 * 1024, ge=1)
    llm_base_url: AnyHttpUrl = AnyHttpUrl("https://openrouter.ai/api/v1")
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = Field(default=30, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
    llm_prompt_version: str = Field(default="v1", min_length=1, max_length=40)

    @field_validator(
        "jwt_secret",
        "admin_email",
        "admin_password",
        "llm_api_key",
        "llm_model",
        "minio_public_endpoint",
        mode="before",
    )
    @classmethod
    def empty_string_is_unset(cls, value: object) -> object:
        return None if value == "" else value

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.database_user, password=self.database_password, host=self.database_host, port=self.database_port, database=self.database_name)

    @property
    def sqlalchemy_async_database_url(self) -> URL:
        return URL.create("postgresql+asyncpg", username=self.database_user, password=self.database_password, host=self.database_host, port=self.database_port, database=self.database_name)

    @property
    def minio_url(self) -> str:
        scheme = "https" if self.minio_secure else "http"
        return f"{scheme}://{self.minio_endpoint}"

    @property
    def minio_public_url(self) -> str:
        scheme = "https" if self.minio_secure else "http"
        endpoint = self.minio_public_endpoint or self.minio_endpoint
        return f"{scheme}://{endpoint}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
