import logging

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from javazone.http.deps import get_db

LOG = logging.getLogger(__name__)

router = APIRouter(
    responses={status.HTTP_404_NOT_FOUND: {"detail": "Not found"}},
)


@router.get("/healthy", status_code=status.HTTP_200_OK)
def liveness(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except OperationalError as e:
        LOG.fatal("Database is not healthy: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    return "Healthy as a fish"


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness():
    return "Ready as an egg"
