import logging
import uuid

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from javazone.http.deps import get_db, get_current_user
from .widgets import router as widgets_router
from .. import schemas
from ...database import models
from ...services import sessions

LOG = logging.getLogger(__name__)

router = APIRouter()
router.include_router(widgets_router, prefix="/widgets", tags=["widgets"])

templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html.j2",
    )


@router.get("/sessions/{id}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def session(
    request: Request, id: uuid.UUID, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = sessions.get(id, db)
    return templates.TemplateResponse(
        request=request,
        name="session.html.j2",
        context={
            "session": schemas.SessionWithUsers.from_db_session(session),
            "user": user,
        },
    )


@router.get("/sessions", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def all_sessions(request: Request, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    all_sessions = [schemas.SessionWithUsers.from_db_session(s) for s in sessions.get_all(db)]
    return templates.TemplateResponse(
        request=request,
        name="sessions.html.j2",
        context={
            "page": _make_sessions_page(all_sessions, "All Sessions", "All sessions at the conference"),
            "user": user,
        },
    )


@router.get("/user/sessions", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def user_sessions(request: Request, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    sess = [
        schemas.SessionWithUsers.from_db_session(s)
        for s in db.query(models.Session).filter(models.Session.users.any(email=user.email)).all()
    ]
    return templates.TemplateResponse(
        request=request,
        name="sessions.html.j2",
        context={
            "page": _make_sessions_page(sess, "My Sessions", "Sessions I am participating in"),
            "user": user,
        },
    )


def _make_sessions_page(all_sessions, title, description):
    page = schemas.SessionsPage(title=title, description=description)
    days = [
        schemas.SessionsDay(id="tuesday", name="Tuesday"),
        schemas.SessionsDay(id="wednesday", name="Wednesday"),
        schemas.SessionsDay(id="thursday", name="Thursday"),
        schemas.SessionsDay(id="tbd", name="TBD"),
    ]

    for session in all_sessions:
        if session.start_time is None:
            days[-1].add_session(session)
        else:
            days[session.start_time.weekday() - 1].add_session(session)
    if len(days[-1].session_slots) < 1:
        del days[-1]
    page.days.extend(days)
    return page
