from typing import Literal

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings

LogLevelStr = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    LOG_LEVEL: LogLevelStr = "INFO"
    PG_ECHO: bool = False

    AUTH_VERIFY: bool = True

    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DATABASE: str = "reviews"
    PG_USERNAME: str = "admin"
    PG_PASSWORD: str = "admin"

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def uppercase_log_level(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value

    model_config = ConfigDict(extra="ignore", env_file=".env", case_sensitive=True)


settings = Settings()
