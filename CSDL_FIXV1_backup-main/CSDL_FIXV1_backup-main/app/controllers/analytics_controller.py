from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/analytics", response_class=HTMLResponse)
async def get_priceboard(request: Request):
    return templates.TemplateResponse("analytics.html", {
        "request": request
    })