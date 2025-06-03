from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.stock import StockModel
from typing import Dict, Any

router = APIRouter()
templates = Jinja2Templates(directory="templates")

symbols = [
    "VCB", "BID", "CTG", "TCB", "MBB", "VPB", "ACB", "HDB", "STB", "EIB",
    "LPB", "SHB", "VIB", "MSB", "OCB", "TPB", "BAB", "ABB", "BVB", "KLB",
    "NAB", "PGB", "SGB", "VAB", "VBB", "SSB", "SCB"
]

@router.get("/stock", response_class=HTMLResponse)
async def get_stock(request: Request, bank_code: str = "VCB") -> HTMLResponse:
    return await get_home(request, bank_code)

async def get_home(request: Request, bank_code: str = "VCB") -> HTMLResponse:
    model = StockModel(bank_code)
    try:
        company_profile, key_developments = model.get_company_profile()
        officers_html = model.get_officers_html()
        shareholders_html = model.get_shareholders_html()
    except Exception:
        company_profile = key_developments = officers_html = shareholders_html = "Không thể tải dữ liệu."

    # Thêm dữ liệu giá
    try:
        price_data = model.get_saved_transactions()
        # Lấy thông tin cổ phiếu mới nhất
        stock_info: Dict[str, Any] = {}
        if price_data:
            stock_info = dict(price_data[0])  # Convert to dict if it's not already
            stock_info['symbol'] = bank_code
            stock_info['company_name'] = model.company.company.profile()['company_name'].iloc[0]
    except Exception:
        price_data = []
        stock_info = {}

    return templates.TemplateResponse("stock.html", {
        "request": request,
        "selected": bank_code,
        "bank_codes": symbols,
        "company_profile": company_profile,
        "key_developments": key_developments,
        "officers_html": officers_html,
        "shareholders_html": shareholders_html,
        "price_data": price_data,
        "stock_info": stock_info
    })
