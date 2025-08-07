from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html.j2")
