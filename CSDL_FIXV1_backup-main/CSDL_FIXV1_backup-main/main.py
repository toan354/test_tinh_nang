from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.controllers.tong_quan_controller import router as priceboard_router, setup_stock_websocket_routes, get_home
from app.controllers.information_controller import router as information_router
from app.controllers.analytics_controller import router as analytics_router
from app.controllers.report_controller import router as report_router
from app.controllers.stock_controller import router as stock_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

setup_stock_websocket_routes(app)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, bank_code: str = "VCB"):
    return await get_home(request, bank_code)

@app.get("/priceboard", response_class=HTMLResponse)
async def priceboard_html(request: Request):
    return templates.TemplateResponse("priceboard.html", {"request": request})

@app.get("/api/information", response_class=HTMLResponse)
async def information_html(request: Request):
    return templates.TemplateResponse("information.html", {"request": request})

@app.get("/report", response_class=HTMLResponse)
async def report_html(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_html(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

# Include all routers
app.include_router(stock_router, prefix="/api")
app.include_router(priceboard_router, prefix="/api")
app.include_router(information_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(report_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)