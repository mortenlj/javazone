import random

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from javazone.http.deps import get_db, get_current_user
from .widgets import router as widgets_router
from .. import schemas
from ...database import models

router = APIRouter()
router.include_router(widgets_router, prefix="/widgets", tags=["widgets"])

templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html.j2",
    )


@router.get("/sessions", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def sessions(request: Request, db: Session = Depends(get_db)):
    all_sessions = [schemas.Session.model_validate_json(s.data) for s in db.query(models.Session).all()]
    return templates.TemplateResponse(
        request=request,
        name="sessions.html.j2",
        context={
            "sessions": _sort_sessions_by_day(all_sessions),
        },
    )


@router.get("/user/sessions", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def user_sessions(request: Request, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    sess = [
        schemas.Session.model_validate_json(s.data)
        for s in db.query(models.Session).filter(models.Session.users.any(email=user.email)).all()
    ]
    return templates.TemplateResponse(
        request=request,
        name="sessions.html.j2",
        context={
            "sessions": _sort_sessions_by_day(sess),
        },
    )


def _sort_sessions_by_day(all_sessions):
    sessions = {
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "TBD": [],
    }
    for session in all_sessions:
        if session.start_time is None:
            sessions["TBD"].append(session)
        elif session.start_time.weekday() == 1:
            sessions["tuesday"].append(session)
        elif session.start_time.weekday() == 2:
            sessions["wednesday"].append(session)
        elif session.start_time.weekday() == 3:
            sessions["thursday"].append(session)
    return sessions
