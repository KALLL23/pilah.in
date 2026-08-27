from functools import lru_cache

from pydantic import Field
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

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.database_user, password=self.database_password, host=self.database_host, port=self.database_port, database=self.database_name)


@lru_cache
def get_settings() -> Settings:
    return Settings()
