import logging

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from javazone.http.deps import get_db, get_current_user
from .widgets import router as widgets_router
from .. import schemas
from ...database import models


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


@router.get("/sessions", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def sessions(request: Request, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    all_sessions = [schemas.SessionWithUsers.from_db_session(s) for s in db.query(models.Session).all()]
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
    days = {
        "tuesday": schemas.SessionsDay(id="tuesday", name="Tuesday"),
        "wednesday": schemas.SessionsDay(id="wednesday", name="Wednesday"),
        "thursday": schemas.SessionsDay(id="thursday", name="Thursday"),
        "TBD": schemas.SessionsDay(id="tbd", name="TBD"),
    }

    def _key(session):
        if session.start_time is None:
            return "9999-12-31T23:59:59"
        return session.start_time.isoformat()

    for session in sorted(all_sessions, key=_key):
        if session.start_time is None:
            days["TBD"].sessions.append(session)
        elif session.start_time.weekday() == 1:
            days["tuesday"].sessions.append(session)
        elif session.start_time.weekday() == 2:
            days["wednesday"].sessions.append(session)
        elif session.start_time.weekday() == 3:
            days["thursday"].sessions.append(session)
    if len(days["TBD"].sessions) < 1:
        del days["TBD"]
    page.days.extend(days.values())
    return page
