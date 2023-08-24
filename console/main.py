#!/usr/bin/env python
import logging
import os
import signal
import sys

import uvicorn
from fastapi import FastAPI
from fiaas_logging import init_logging

from console import api, gql
from console.core.config import settings

LOG = logging.getLogger(__name__)


app = FastAPI(title="NAIS management console")
app.include_router(api.router, prefix="/api")
app.include_router(gql.graphql_app, prefix="/graphql")


class ExitOnSignal(Exception):
    pass


def main():
    _init_logging(settings.debug)
    exit_code = 0
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        LOG.info("Starting console")
        uvicorn.run(
            "console.main:app",
            host=settings.bind_address,
            port=settings.port,
            log_config=None,
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


def _init_logging(debug):
    if os.getenv("NAIS_CLIENT_ID"):
        init_logging(format="json", debug=debug)
    else:
        init_logging(debug=debug)
    return logging.getLogger().getEffectiveLevel()


if __name__ == "__main__":
    sys.exit(main())
