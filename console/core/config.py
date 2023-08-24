from enum import Enum

from pydantic import BaseSettings, PostgresDsn, validator


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"

    def __new__(cls, value):
        return super().__new__(cls, value.lower())


class Settings(BaseSettings):
    class Config:
        env_prefix = "CONSOLE_"

    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000
    database_url: PostgresDsn = "postgres://postgres:postgres@localhost:5432/postgres"

    @property
    def debug(self):
        return self.mode == Mode.DEBUG

    @validator("database_url")
    def fix_postgres_scheme(cls, v):
        return v.replace("postgres:", "postgresql:", 1)


settings = Settings()
