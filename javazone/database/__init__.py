import datetime
import os

import functools
from argparse import Namespace

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from javazone.core.config import settings

Base = declarative_base()


@functools.cache
def init():
    engine = create_engine(settings.database_url)

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    session_maker = init()
    return session_maker()
