from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Query
from app.services.information_service import (
    get_all_stocks,
    get_all_report_types,
    get_line_items_by_report_type,
    fetch_financial_data
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/stocks")
async def stocks():
    return await get_all_stocks()

@router.get("/report_types")
async def report_types():
    return await get_all_report_types()

@router.get("/line_items")
async def line_items(report_type_id: int):
    return await get_line_items_by_report_type(report_type_id)

@router.get("/financial_data")
async def financial_data(
    symbol: str = Query(...),
    report_type_id: int = Query(...),
    period: str = Query("yearly")
):
    return await fetch_financial_data(symbol, report_type_id, period)


