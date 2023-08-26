#!/usr/bin/env python
import logging
import signal
import sys

import uvicorn
from fastapi import FastAPI

from javazone import api
from javazone.core.config import settings
from javazone.core.logging import get_log_config
from javazone.database import init_db

LOG = logging.getLogger(__name__)
TITLE = "JavaZone calendar manager"

app = FastAPI(title=TITLE, lifespan=init_db)
app.include_router(api.router, prefix="/api")


class ExitOnSignal(Exception):
    pass


def main():
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = "plain"
    exit_code = 0
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        LOG.info(f"Starting {TITLE} with configuration {settings}")
        uvicorn.run(
            "javazone.main:app",
            host=settings.bind_address,
            port=settings.port,
            log_config=get_log_config(log_format),
            log_level=log_level,
            reload=settings.debug,
            access_log=settings.debug,
        )
    except ExitOnSignal:
        pass
    except Exception as e:
        logging.exception(f"unwanted exception: {e}")
        exit_code = 113
    return exit_code


def signal_handler(signum, frame):
    raise ExitOnSignal()


if __name__ == "__main__":
    sys.exit(main())
