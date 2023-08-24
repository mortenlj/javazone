from console.database import get_session


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


# Trigger database init on import
_ = get_session()
