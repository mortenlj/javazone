from fastapi import APIRouter, status

from . import v1

router = APIRouter()
router.include_router(v1.router, prefix="/v1")


@router.get("/ping", status_code=status.HTTP_200_OK)
def readiness():
    return "pong"
