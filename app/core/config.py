import os
from enum import Enum
from functools import lru_cache

from dotenv import dotenv_values
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


def current_env() -> Environment:
    value = os.getenv("APP_ENV") or dotenv_values(".env").get("APP_ENV")
    return Environment((value or Environment.SANDBOX.value).strip().lower())


def env_files(env: Environment) -> tuple[str, ...]:
    return (".env", f".env.{env.value}")


class Settings(BaseSettings):
    app_env: Environment = Environment.SANDBOX
    debug: bool = False
    docs_enabled: bool = True
    log_level: str = "INFO"

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 10

    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(extra="ignore")

    @model_validator(mode="after")
    def check_production_safety(self) -> "Settings":
        if self.app_env == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("DEBUG має бути вимкнено у production")
            if len(self.secret_key) < 32 or "change-me" in self.secret_key:
                raise ValueError(
                    "У production SECRET_KEY має бути випадковим рядком "
                    "довжиною від 32 символів"
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def db_pool_capacity(self) -> int:
        return self.db_pool_size + self.db_max_overflow

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    env = current_env()
    return Settings(_env_file=env_files(env), app_env=env)


settings = get_settings()
