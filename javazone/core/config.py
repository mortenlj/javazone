from enum import Enum

from pydantic import BaseSettings, AnyUrl


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"

    def __new__(cls, value):
        return super().__new__(cls, value.lower())


class Settings(BaseSettings):
    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000
    database_url: AnyUrl = "mysql+pymysql://javazone:password@localhost:3306/javazone"

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
