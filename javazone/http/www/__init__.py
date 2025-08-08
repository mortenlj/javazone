from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from javazone.http import schemas
from javazone.http.deps import get_user_or_none

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def index(request: Request, user: schemas.User = Depends(get_user_or_none)):
    return templates.TemplateResponse(
        request=request,
        name="index.html.j2",
        context={
            "user": user,
        },
    )


@router.get("/login", status_code=status.HTTP_200_OK, response_class=RedirectResponse)
def login(redirect_url: str = "/"):
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
