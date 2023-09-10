#!/usr/bin/env python
import logging
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from javazone import api
from javazone.core.config import settings
from javazone.core.logging import get_log_config
from javazone.database import init_db
from javazone.security import init_jwt

LOG = logging.getLogger(__name__)
TITLE = "JavaZone calendar manager"


class ExitOnSignal(Exception):
    pass


@asynccontextmanager
async def on_startup(app: FastAPI):
    async with init_db(app):
        async with init_jwt(app):
            yield


app = FastAPI(title=TITLE, lifespan=on_startup)
app.include_router(api.router, prefix="/api")


def main():
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = "plain"
    exit_code = 0
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        print(f"Starting {TITLE} with configuration {settings}")
        uvicorn.run(
            "javazone.main:app",
            host=settings.bind_address,
            port=settings.port,
            log_config=get_log_config(log_format, log_level),
            log_level=log_level,
            reload=settings.debug,
            access_log=settings.debug,
        )
    except ExitOnSignal:
        pass
    except Exception as e:
        print(f"unwanted exception: {e}")
        exit_code = 113
    return exit_code


def signal_handler(signum, frame):
    raise ExitOnSignal()


if __name__ == "__main__":
    sys.exit(main())
