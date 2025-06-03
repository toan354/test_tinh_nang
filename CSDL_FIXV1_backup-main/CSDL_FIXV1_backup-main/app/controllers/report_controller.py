from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/report", response_class=HTMLResponse)
async def get_priceboard(request: Request):
    return templates.TemplateResponse("report.html", {
        "request": request
    })