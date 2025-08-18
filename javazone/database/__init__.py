import functools

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from javazone.core.config import settings

Base = declarative_base()


@functools.cache
def init():
    from . import models  # NOQA F401: Imported here for side effect of loading Base subclasses

    engine = create_engine(settings.database.dsn(), pool_pre_ping=True, pool_size=10, max_overflow=20)
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    session_maker = init()
    return session_maker()
