from functools import lru_cache

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
    jwt_secret: SecretStr | None = None
    llm_base_url: AnyHttpUrl = AnyHttpUrl("https://openrouter.ai/api/v1")
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = Field(default=30, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
    llm_prompt_version: str = Field(default="v1", min_length=1, max_length=40)

    @field_validator("jwt_secret", "llm_api_key", "llm_model", mode="before")
    @classmethod
    def empty_string_is_unset(cls, value: object) -> object:
        return None if value == "" else value

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.database_user, password=self.database_password, host=self.database_host, port=self.database_port, database=self.database_name)

    @property
    def sqlalchemy_async_database_url(self) -> URL:
        return URL.create("postgresql+asyncpg", username=self.database_user, password=self.database_password, host=self.database_host, port=self.database_port, database=self.database_name)


@lru_cache
def get_settings() -> Settings:
    return Settings()
