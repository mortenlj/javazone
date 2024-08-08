import datetime
from enum import Enum

from furl import furl
from pydantic import AnyUrl, BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class DatabaseSettings(BaseModel):
    username: str = None
    password: SecretStr = None
    url: AnyUrl = AnyUrl("mysql+pymysql://javazone:password@localhost:3306/javazone")

    def dsn(self):
        if self.url.scheme == "sqlite":
            return self.url
        url = furl(self.url)
        if self.username and not url.username:
            url.username = self.username
        if self.password and self.password.get_secret_value() and not url.password:
            url.password = self.password.get_secret_value()
        if url.scheme == "postgres":
            url.scheme = "postgresql"
        return str(url)


class GoogleOAuthSettings(BaseModel):
    client_id: str
    client_secret: SecretStr


class Settings(BaseSettings):
    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    oauth: GoogleOAuthSettings = Field(default_factory=GoogleOAuthSettings)
    year: int = datetime.date.today().year
    root_path: str = ""

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
