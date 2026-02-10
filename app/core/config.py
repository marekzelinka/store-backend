import re
from typing import Annotated

from pydantic import PostgresDsn, SecretStr, UrlConstraints, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


config = Settings()
