import logging
from app.models.information import client, HEADERS, SUPABASE_URL
from fastapi.templating import Jinja2Templates



logger = logging.getLogger(__name__)

async def get_all_stocks():
    res = await client.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=HEADERS)
    return res.json()

async def get_all_report_types():
    res = await client.get(f"{SUPABASE_URL}/rest/v1/report_types", headers=HEADERS)
    return res.json()

async def get_line_items_by_report_type(report_type_id: int):
    res = await client.get(
        f"{SUPABASE_URL}/rest/v1/line_items?report_type_id=eq.{report_type_id}",
        headers=HEADERS
    )
    return res.json()

async def fetch_financial_data(symbol: str, report_type_id: int, period: str):
    # Get stock_id
    stock_res = await client.get(
        f"{SUPABASE_URL}/rest/v1/stocks?symbol=eq.{symbol}", headers=HEADERS
    )
    stock_data = stock_res.json()
    if not stock_data:
        logger.error(f"Symbol {symbol} not found")
        return {"error": "Symbol not found"}
    stock_id = stock_data[0]['stock_id']

    # Get line items
    li_res = await client.get(
        f"{SUPABASE_URL}/rest/v1/line_items?report_type_id=eq.{report_type_id}",
        headers=HEADERS
    )
    line_items = li_res.json()
    line_item_id_to_name = {li['line_item_id']: li['line_item_name'] for li in line_items}

    # Conditions
    year_condition = "&year=gte.2020&year=lte.2024"
    quarter_condition = "&quarter=in.(Q1,Q2,Q3,Q4)" if period == "quarterly" else ""

    # Get financial_reports
    query_url = (
        f"{SUPABASE_URL}/rest/v1/financial_reports"
        f"?stock_id=eq.{stock_id}&report_type_id=eq.{report_type_id}"
        f"{year_condition}{quarter_condition}"
    )
    fr_res = await client.get(query_url, headers=HEADERS)
    reports = fr_res.json()
    if not reports:
        return {"error": "No reports found"}

    report_id_to_time = {
        r['report_id']: f"{r['year']}Q{r['quarter'][1]}" if period == "quarterly" else str(r['year'])
        for r in reports
    }

    report_ids = [r['report_id'] for r in reports]
    report_ids_str = ','.join(map(str, report_ids))

    # Get financial_data
    fd_res = await client.get(
        f"{SUPABASE_URL}/rest/v1/financial_data?report_id=in.({report_ids_str})",
        headers=HEADERS
    )
    financial_data = fd_res.json()

    # Merge data
    result = {}
    for fd in financial_data:
        line_item = line_item_id_to_name.get(fd['line_item_id'], "Unknown")
        time_key = report_id_to_time.get(fd['report_id'])
        if not time_key:
            continue
        result.setdefault(line_item, {})[time_key] = fd['value']

    # Format response
    response = []
    for item, values in result.items():
        row = {"item": item}
        if period == "yearly":
            for y in range(2020, 2025):
                row[str(y)] = values.get(str(y))
        else:
            for y in range(2020, 2025):
                for q in range(1, 5):
                    key = f"{y}Q{q}"
                    row[key] = values.get(key)
        response.append(row)

    return response
