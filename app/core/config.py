import re
from typing import Annotated

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    SecretStr,
    UrlConstraints,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: str | list[str] | None) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list | str):
        return v

    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: Annotated[
        MultiHostUrl,
        UrlConstraints(allowed_schemes=["postgresql"]),
    ]

    @computed_field
    @property
    def sqlalchemy_database_url(self) -> PostgresDsn:
        """
        Sets up a db connection URL for both SQLAlchemy and Alembic.
        Removes libpq-specific params like 'channel_binding' and 'sslmode'
        that break asyncpg.
        """
        url = str(self.database_url)
        url = re.sub(r"^postgresql:", "postgresql+asyncpg:", url)
        url = url.replace("sslmode=require", "ssl=require")
        url = re.sub(r"[?&]channel_binding=[^&]*", "", url)

        return PostgresDsn(url)

    # CORS
    cors_origins: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.cors_origins]

    # Auth
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 Days

    # Admin
    first_admin: str
    first_admin_email: EmailStr
    first_admin_password: SecretStr


config = Settings()
