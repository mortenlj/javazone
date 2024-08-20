#!/usr/bin/env python
import logging
import signal
from contextlib import asynccontextmanager

import anyio
import sys
import uvicorn
from anyio import create_task_group
from fastapi import FastAPI

from javazone import api
from javazone.api import probes
from javazone.core.config import settings
from javazone.core.logging import get_log_config
from javazone.database import init as init_db
from javazone.security import init_jwt

LOG = logging.getLogger(__name__)
TITLE = "JavaZone calendar manager"


class ExitOnSignal(Exception):
    pass


async def my_task():
    LOG.info("Starting my task")
    await anyio.sleep(5)
    LOG.info("My task completed")


async def run_repeating_background_task(interval, tg):
    while True:
        await anyio.sleep(interval)
        tg.start_soon(my_task)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_jwt()
    async with create_task_group() as tg:
        tg.start_soon(run_repeating_background_task, 10, tg)
        yield
        tg.cancel_scope.cancel()


app = FastAPI(title=TITLE, lifespan=lifespan)
app.include_router(api.router, prefix="/api")
app.include_router(probes.router, prefix="/_")


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
            proxy_headers=True,
            root_path=settings.root_path,
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
