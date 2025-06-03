# app/models/tong_quan_model.py
"""
Tổng hợp các model: stock_model.py, market_data.py, index_model.py, financial_data.py
"""

# ==== MARKET DATA MODEL (from market_data.py) ====
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging
import pandas as pd

class MarketCapItem(BaseModel):
    """
    Định nghĩa cấu trúc dữ liệu cho một mục vốn hóa thị trường
    """
    symbol: str
    value: float

class MarketCapResponse(BaseModel):
    """
    Định nghĩa cấu trúc dữ liệu trả về cho API vốn hóa thị trường
    """
    data: List[MarketCapItem]

# ==== FINANCIAL DATA MODEL (from financial_data.py) ====
class FinancialDataPoint(BaseModel):
    """
    Pydantic model đại diện cho một điểm dữ liệu tài chính trả về từ API.
    Sử dụng cho validation dữ liệu và tài liệu Swagger.
    """
    symbol: str = Field(..., description="Mã chứng khoán", examples=["ACB", "VCB"])
    value: float = Field(..., description="Giá trị tài chính tương ứng", examples=[150000.5])

# ==== INDEX MODEL (from index_model.py) ====
# (index_model.py chỉ có pass, không cần thêm gì)

# ==== STOCK MODEL (from stock_model.py) ====
class StockModel:
    def __init__(self):
        from vnstock import Vnstock
        self.stock_client = Vnstock()
        self.symbols = ['VCB', 'BID', 'CTG', 'TCB', 'MBB', 'VPB', 'ACB', 'HDB', 'STB',
                        'EIB', 'LPB', 'SHB', 'VIB', 'MSB', 'OCB', 'TPB', 'BAB', 'ABB',
                        'BVB', 'KLB', 'NAB', 'PGB', 'SGB', 'VAB', 'VBB', 'SSB', 'SCB']
    async def fetch_stock_data(self):
        price_board = pd.DataFrame()
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"Đang lấy dữ liệu cho các mã: {self.symbols}")
            if not self.symbols:
                logger.error("Danh sách mã chứng khoán (self.symbols) trống.")
                return {"error": "Danh sách mã chứng khoán trống."}
            stock_obj = self.stock_client.stock(symbol='VN30F1M', source='VCI')
            price_board = stock_obj.trading.price_board(symbols_list=self.symbols)
            if price_board is None or price_board.empty:
                logger.warning("Không có dữ liệu từ vnstock hoặc dữ liệu trống.")
                return {"error": "Không có dữ liệu từ vnstock hoặc dữ liệu trống."}
            col_symbol = ('listing', 'symbol')
            col_match_price = ('match', 'match_price')
            col_prior_close = ('listing', 'ref_price')
            col_volume = ('match', 'accumulated_volume')
            required_cols_tuples = [col_symbol, col_match_price, col_prior_close, col_volume]
            missing_cols = [col for col in required_cols_tuples if col not in price_board.columns]
            if missing_cols:
                logger.error(f"Thiếu các cột MultiIndex cần thiết: {missing_cols}")
                logger.error(f"Các cột MultiIndex hiện có trong DataFrame: {price_board.columns.tolist()}")
                return {"error": f"Lỗi nội bộ: Thiếu cột {missing_cols}. Các cột có sẵn: {price_board.columns.tolist()}"}
            result = price_board[required_cols_tuples].copy()
            result.columns = ['symbol', 'current_price', 'prior_close', 'volume']
            for col in ['current_price', 'prior_close', 'volume']:
                result[col] = pd.to_numeric(result[col], errors='coerce')
            result['price_change'] = result['current_price'] - result['prior_close']
            result['percent_change'] = result.apply(
                lambda row: round((row['price_change'] / row['prior_close'] * 100), 2)
                if pd.notnull(row['prior_close']) and row['prior_close'] != 0 and pd.notnull(row['price_change'])
                else None,
                axis=1
            )
            result = result.astype(object).where(pd.notnull(result), None)
            return result.to_dict(orient='records')
        except AttributeError as e:
            if "'float' object has no attribute 'round'" in str(e):
                logger.error(f"Lỗi làm tròn số: {e}. Đảm bảo sử dụng hàm round() đúng cách cho float.", exc_info=True)
            else:
                logger.error(f"AttributeError khi lấy dữ liệu: {e}. Có thể phương thức API vnstock đã thay đổi hoặc gọi sai.", exc_info=True)
            return {"error": f"Lỗi thuộc tính (AttributeError): {str(e)}."}
        except KeyError as e:
            logger.error(f"KeyError khi xử lý dữ liệu: {e}. Kiểm tra lại tên cột.", exc_info=True)
            if not price_board.empty:
                 logger.error(f"Các cột có trong price_board: {price_board.columns.tolist()}")
            else:
                 logger.error("price_board trống hoặc không được tạo.")
            return {"error": f"Lỗi xử lý dữ liệu (KeyError): {str(e)}."}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi lấy dữ liệu: {e}", exc_info=True)
            return {"error": f"Lỗi không xác định: {str(e)}"} 