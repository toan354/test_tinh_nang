# app/services/tong_quan_service.py
"""
Tổng hợp các service: tong_von_hoa_service.py, financial_service.py, index_service.py, market_data_service.py, news_service.py
"""
# ==== IMPORT CHUNG ====
from supabase import Client
from fastapi import Depends, HTTPException
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
from datetime import datetime, timedelta
from starlette.websockets import WebSocketState
from fastapi.templating import Jinja2Templates
from app.config import get_supabase_client, settings
from app.models.tong_quan_model import MarketCapItem, FinancialDataPoint, StockModel
from vnstock import Vnstock

logger = logging.getLogger(__name__)

# ==== TỔNG VỐN HÓA SERVICE (from tong_von_hoa_service.py) ====
def calculate_total_capital_for_all_stocks(
    year: int,
    quarter: str,
    line_item_id: int
) -> float:
    supabase = get_supabase_client()
    total_value = 0.0
    logger.info(f"Service: Calculating total capital for year={year}, quarter='{quarter}', line_item_id={line_item_id}")
    try:
        reports_response = supabase.table("financial_reports") \
            .select("report_id") \
            .eq("year", year) \
            .eq("quarter", quarter) \
            .execute()
        if hasattr(reports_response, 'error') and reports_response.error:
            logger.error(f"Supabase error fetching reports: {reports_response.error}")
            raise Exception(f"Supabase error fetching reports: {reports_response.error.message}")
        if not reports_response.data:
            logger.warning(f"Không tìm thấy báo cáo tài chính cho năm {year} và quý {quarter}.")
            return 0.0
        report_ids = [report['report_id'] for report in reports_response.data]
        if not report_ids:
            logger.warning("Danh sách report_id trống sau khi query financial_reports.")
            return 0.0
        logger.debug(f"Found {len(report_ids)} report_ids: {report_ids[:5]}...")
        financial_data_response = supabase.table("financial_data") \
            .select("value") \
            .in_("report_id", report_ids) \
            .eq("line_item_id", line_item_id) \
            .execute()
        if hasattr(financial_data_response, 'error') and financial_data_response.error:
            logger.error(f"Supabase error fetching financial_data: {financial_data_response.error}")
            raise Exception(f"Supabase error fetching financial_data: {financial_data_response.error.message}")
        if financial_data_response.data:
            for item in financial_data_response.data:
                if item.get('value') is not None:
                    try:
                        total_value += float(item['value'])
                    except ValueError:
                        logger.warning(f"Giá trị không hợp lệ được bỏ qua trong financial_data: {item.get('value')}")
            logger.info(f"Calculated total_value: {total_value} from {len(financial_data_response.data)} items.")
        else:
            logger.warning(f"Không tìm thấy dữ liệu tài chính (financial_data) cho line_item_id {line_item_id} trong các report_ids đã chọn.")
    except Exception as e:
        logger.exception(f"Đã xảy ra lỗi trong quá trình tính toán tổng nguồn vốn: {e}")
        raise 
    return total_value

# ==== FINANCIAL SERVICE (from financial_service.py) ====
class FinancialService:
    def __init__(self, db_client: Client = Depends(get_supabase_client)):
        self.db = db_client
        logger.debug("FinancialService initialized with Supabase client.")
    async def get_chart_data(self, line_item_id: int) -> List[FinancialDataPoint]:
        rpc_function_name = 'get_financial_data_for_chart'
        rpc_params = {
            'p_line_item_id': line_item_id,
            'p_year': 2024,
            'p_quarter': 'Q4'
        }
        logger.info(f"Service: Calling RPC '{rpc_function_name}' for line_item_id={line_item_id}")
        try:
            response = self.db.rpc(rpc_function_name, rpc_params).execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"Service: Supabase RPC error response: {response.error}")
                error_details = response.error.get('message', 'Unknown database error')
                raise HTTPException(
                    status_code=500,
                    detail=f"Database RPC Error: {error_details}"
                )
            data = response.data if response.data else []
            logger.info(f"Service: RPC call successful. Received {len(data)} data points for line_item_id={line_item_id}.")
            return data
        except Exception as e:
            logger.exception(f"Service: Unexpected error during RPC call for line_item_id={line_item_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal Server Error while fetching financial data"
            )

# ==== INDEX SERVICE (from index_service.py) ====
class IndexService:
    def __init__(self):
        try:
            self.supabase: Client = get_supabase_client()
            logger.info("IndexService initialized and Supabase client obtained.")
        except Exception as e:
            logger.error(f"IndexService failed to initialize Supabase client: {e}", exc_info=True)
            raise
        self.INDEX_CONFIG: Dict[str, Dict[str, any]] = settings.INDEX_CONFIG.copy()
        if not self.INDEX_CONFIG:
            logger.warning("INDEX_CONFIG is empty in settings. Index processing might not work as expected.")
        else:
            logger.info(f"IndexService loaded INDEX_CONFIG: {list(self.INDEX_CONFIG.keys())}")
        self._initialize_index_type_ids()

    def _initialize_index_type_ids(self):
        if not self.INDEX_CONFIG:
            return
        logger.info("Initializing index_type_ids from 'index_types' table...")
        try:
            response = self.supabase.table('index_types').select('id, index_type').execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error fetching from 'index_types' table: {response.error}")
                return
            if response.data:
                type_map = {item['index_type']: item['id'] for item in response.data}
                updated_configs = 0
                for index_name, config in self.INDEX_CONFIG.items():
                    index_type_from_config = config.get('index_type')
                    if index_type_from_config in type_map:
                        config['index_type_id'] = type_map[index_type_from_config]
                        logger.debug(f"Assigned index_type_id={config['index_type_id']} for {index_name}")
                        updated_configs +=1
                    else:
                        logger.warning(f"No 'index_type_id' found for index_type '{index_type_from_config}' (config: {index_name}) in 'index_types' table.")
                if updated_configs > 0:
                    logger.info(f"Successfully updated {updated_configs} index_type_ids from database.")
                else:
                    logger.warning("No index_type_ids were updated. Check 'index_types' table and INDEX_CONFIG.")
            else:
                logger.warning("No data returned from 'index_types' table. Cannot initialize index_type_ids.")
        except Exception as e:
            logger.error(f"Exception while fetching or processing 'index_types' data: {e}", exc_info=True)

    def _fetch_from_vnstock(self, symbol: str, source: str, start_date: str, end_date: str) -> pd.DataFrame:
        logger.info(f"Fetching data from vnstock3 for {symbol} (source: {source}) from {start_date} to {end_date}")
        try:
            stock_data_fetcher = Vnstock().stock(symbol=symbol, source=source)
            df = stock_data_fetcher.quote.history(start=start_date, end=end_date)
            if df is None:
                logger.warning(f"vnstock3 returned None for {symbol} from {start_date} to {end_date}.")
                return pd.DataFrame()
            if df.empty:
                logger.info(f"No new data from vnstock3 for {symbol} from {start_date} to {end_date}.")
                return pd.DataFrame()
            if 'time' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
            if 'time' not in df.columns:
                logger.error(f"Column 'time' not found in vnstock3 data for {symbol}. Columns: {df.columns.tolist()}")
                return pd.DataFrame()
            df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
            df = df.sort_values('time').reset_index(drop=True)
            required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in data from vnstock for {symbol}: {missing_cols}. Available: {df.columns.tolist()}")
            existing_required_cols = [col for col in required_cols if col in df.columns]
            df_filtered = df[existing_required_cols].copy()
            logger.info(f"Successfully fetched {len(df_filtered)} rows from vnstock3 for {symbol}.")
            return df_filtered
        except Exception as vnstock_error:
            logger.error(f"Error fetching data from vnstock3 for {symbol}: {vnstock_error}", exc_info=True)
            return pd.DataFrame()

    def _get_latest_date_from_db(self, index_type_id: int) -> Optional[str]:
        if index_type_id is None:
            logger.warning("index_type_id is None, cannot fetch latest date from DB.")
            return None
        logger.debug(f"Fetching latest date from DB for index_type_id: {index_type_id}")
        latest_date_to_start_fetch = None
        try:
            response = self.supabase.table('index_history')\
                .select('time')\
                .eq('index_type_id', index_type_id)\
                .order('time', desc=True)\
                .limit(1)\
                .execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"DB Error fetching latest date for index_type_id {index_type_id}: {response.error}")
                return None
            if response.data:
                latest_date_in_db_str = response.data[0]['time']
                latest_date_obj = datetime.strptime(latest_date_in_db_str, '%Y-%m-%d')
                next_day_obj = latest_date_obj + timedelta(days=1)
                latest_date_to_start_fetch = next_day_obj.strftime('%Y-%m-%d')
                logger.info(f"Latest date in DB for index_type_id {index_type_id} is {latest_date_in_db_str}. Next fetch starts from: {latest_date_to_start_fetch}")
            else:
                logger.info(f"No existing data in DB for index_type_id {index_type_id}. Will fetch from default start date.")
        except Exception as query_error:
            logger.error(f"Exception while fetching latest date for index_type_id {index_type_id}: {query_error}", exc_info=True)
        return latest_date_to_start_fetch

    def _save_to_supabase(self, df_new: pd.DataFrame, index_type_id: int, index_type_name: str) -> int:
        if df_new.empty:
            logger.info(f"No new data to save for {index_type_name} (ID: {index_type_id}).")
            return 0
        if index_type_id is None:
            logger.error(f"Cannot save data for {index_type_name} because index_type_id is None.")
            return 0
        logger.info(f"Preparing to save {len(df_new)} new records for {index_type_name} (ID: {index_type_id}) to Supabase.")
        records_to_insert: List[Dict[str, any]] = []
        for _, row in df_new.iterrows():
            try:
                record = {
                    'index_type_id': int(index_type_id),
                    'time': row['time'],
                    'open': float(row['open']) if pd.notna(row.get('open')) else None,
                    'high': float(row['high']) if pd.notna(row.get('high')) else None,
                    'low': float(row['low']) if pd.notna(row.get('low')) else None,
                    'close': float(row['close']) if pd.notna(row.get('close')) else None,
                    'volume': int(row['volume']) if pd.notna(row.get('volume')) else None
                }
                if record['time'] is None or record['close'] is None:
                    logger.warning(f"Skipping record for {index_type_name} due to missing time/close: {row.to_dict()}")
                    continue
                records_to_insert.append(record)
            except Exception as convert_error:
                logger.error(f"Error converting data for row in {index_type_name} (Date: {row.get('time', 'N/A')}): {convert_error}. Row: {row.to_dict()}", exc_info=True)
                continue
        if not records_to_insert:
            logger.info(f"No valid records to insert for {index_type_name} after conversion/validation.")
            return 0
        saved_count = 0
        try:
            min_date = df_new['time'].min()
            max_date = df_new['time'].max()
            existing_response = self.supabase.table('index_history')\
                                    .select('time')\
                                    .eq('index_type_id', index_type_id)\
                                    .gte('time', min_date)\
                                    .lte('time', max_date)\
                                    .execute()
            existing_dates = set()
            if hasattr(existing_response, 'data') and existing_response.data:
                existing_dates = {rec['time'] for rec in existing_response.data}
            final_records_to_insert = [rec for rec in records_to_insert if rec['time'] not in existing_dates]
            if not final_records_to_insert:
                logger.info(f"All {len(records_to_insert)} new records for {index_type_name} already exist in the database.")
                return 0
            logger.info(f"Attempting to insert {len(final_records_to_insert)} genuinely new records for {index_type_name}.")
            response = self.supabase.table('index_history').insert(final_records_to_insert).execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error inserting batch data into 'index_history' for {index_type_name}: {response.error}")
            elif response.data:
                saved_count = len(response.data)
                logger.info(f"Successfully saved {saved_count} new records to 'index_history' for {index_type_name}.")
            else:
                 logger.info(f"Batch insert for {index_type_name} executed, assuming success (no data returned in response, no error). Count: {len(final_records_to_insert)}")
                 saved_count = len(final_records_to_insert)
        except Exception as insert_error:
            logger.error(f"Unexpected exception during batch insert for {index_type_name}: {insert_error}", exc_info=True)
        return saved_count

    def _get_all_data_from_db(self, index_type_id: int, index_type_name: str) -> pd.DataFrame:
        if index_type_id is None:
            logger.warning(f"index_type_id is None for {index_type_name}, cannot fetch data from DB.")
            return pd.DataFrame()
        logger.info(f"Fetching all data from DB for {index_type_name} (ID: {index_type_id})")
        try:
            response = self.supabase.table('index_history')\
                .select('time, open, high, low, close, volume')\
                .eq('index_type_id', index_type_id)\
                .order('time', desc=False)\
                .execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"DB Error fetching all data for {index_type_name} (ID: {index_type_id}): {response.error}")
                return pd.DataFrame()
            if not response.data:
                logger.warning(f"No data found in 'index_history' for {index_type_name} (ID: {index_type_id})")
                return pd.DataFrame()
            df_supabase = pd.DataFrame(response.data)
            for col in ['open', 'high', 'low', 'close']:
                if col in df_supabase.columns:
                    df_supabase[col] = pd.to_numeric(df_supabase[col], errors='coerce')
            if 'volume' in df_supabase.columns:
                 df_supabase['volume'] = pd.to_numeric(df_supabase['volume'], errors='coerce').astype('Int64')
            if 'time' in df_supabase.columns:
                df_supabase['time'] = pd.to_datetime(df_supabase['time']).dt.strftime('%Y-%m-%d')
            df_supabase = df_supabase.sort_values('time').reset_index(drop=True)
            logger.info(f"Successfully fetched {len(df_supabase)} total rows from 'index_history' for {index_type_name} (ID: {index_type_id}).")
            return df_supabase
        except Exception as query_error:
            logger.error(f"Exception fetching all data for {index_type_name} (ID: {index_type_id}): {query_error}", exc_info=True)
            return pd.DataFrame()

    def get_and_update_index_data(self, index_symbol: str, index_type_name: str, source_api: str) -> pd.DataFrame:
        config = self.INDEX_CONFIG.get(index_symbol)
        if not config:
            logger.error(f"No configuration found for index_symbol: {index_symbol}. Cannot process.")
            return pd.DataFrame()
        index_type_id = config.get('index_type_id')
        if index_type_id is None:
            logger.error(f"index_type_id is not initialized for {index_symbol} (type: {index_type_name}). Check 'index_types' table and config. Skipping update for this index.")
            return self._get_all_data_from_db(None, index_type_name)
        logger.info(f"Processing index: {index_symbol} (Type: {index_type_name}, ID: {index_type_id}, Source: {source_api})")
        start_date_for_fetch = self._get_latest_date_from_db(index_type_id)
        if start_date_for_fetch is None:
            default_start_date = '2024-01-01'
            if settings.INDEX_CONFIG and index_symbol in settings.INDEX_CONFIG and 'default_start_date' in settings.INDEX_CONFIG[index_symbol]:
                default_start_date = settings.INDEX_CONFIG[index_symbol]['default_start_date']
            start_date_for_fetch = default_start_date
            logger.info(f"No existing data or failed to get latest date for {index_symbol}. Using default/configured start date: {start_date_for_fetch}")
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        df_new_from_api = pd.DataFrame()
        if start_date_for_fetch <= current_date_str:
            df_new_from_api = self._fetch_from_vnstock(index_symbol, source_api, start_date_for_fetch, current_date_str)
        else:
            logger.info(f"Start date {start_date_for_fetch} is after current date {current_date_str}. No new data to fetch for {index_symbol}.")
        if not df_new_from_api.empty:
            for col_numeric in ['open', 'high', 'low', 'close', 'volume']:
                if col_numeric in df_new_from_api.columns:
                    df_new_from_api[col_numeric] = pd.to_numeric(df_new_from_api[col_numeric], errors='coerce')
            num_saved = self._save_to_supabase(df_new_from_api, index_type_id, index_type_name)
            logger.info(f"{num_saved} new records saved for {index_symbol}.")
        else:
            logger.info(f"No new data fetched from API for {index_symbol} to save.")
        df_all_from_db = self._get_all_data_from_db(index_type_id, index_type_name)
        return df_all_from_db

    def process_index_data_for_display(self, df: pd.DataFrame, symbol: str) -> Dict[str, any]:
        if df is None or df.empty:
            logger.warning(f"Input DataFrame for display processing is empty or None for {symbol}.")
            return {
                'status': 'error',
                'message': f'No data available to process for display for {symbol}.',
                'name': symbol, 'category': 'index', 'latest_close': None,
                'change': None, 'change_percent': None, 'mini_chart_data': []
            }
        df = df.sort_values('time').reset_index(drop=True)
        for col in ['close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df_cleaned = df.dropna(subset=['close']).copy()
        if df_cleaned.empty:
            logger.warning(f"DataFrame for {symbol} is empty after dropping NaNs in 'close' column.")
            return {
                'status': 'warning',
                'message': f'Not enough valid data points to calculate changes for {symbol} after cleaning.',
                'name': symbol, 'category': 'index', 'latest_close': None,
                'change': None, 'change_percent': None,
                'mini_chart_data': df[['time', 'close']].tail(30).to_dict(orient='records')
            }
        try:
            latest_close = float(df_cleaned['close'].iloc[-1])
            previous_close = float(df_cleaned['close'].iloc[-2]) if len(df_cleaned) > 1 else latest_close
            change = round(latest_close - previous_close, 2)
            change_percent = round((change / previous_close) * 100, 3) if previous_close != 0 else 0.0
            mini_chart_data_df = df_cleaned[['time', 'close']].tail(30)
            mini_chart_data_df['close'] = mini_chart_data_df['close'].apply(lambda x: None if pd.isna(x) else x)
            mini_chart_data: List[Dict[str, any]] = mini_chart_data_df.to_dict(orient='records')
            return {
                'status': 'success',
                'name': symbol,
                'category': 'index',
                'latest_close': latest_close if pd.notna(latest_close) else None,
                'change': change if pd.notna(change) else None,
                'change_percent': change_percent if pd.notna(change_percent) else None,
                'mini_chart_data': mini_chart_data
            }
        except IndexError:
             logger.warning(f"IndexError during display processing for {symbol}, likely due to insufficient data points after cleaning. Len: {len(df_cleaned)}")
             latest_close_val = float(df_cleaned['close'].iloc[-1]) if not df_cleaned.empty else None
             raw_mini_chart = df_cleaned[['time', 'close']].tail(30).to_dict(orient='records') if not df_cleaned.empty else []
             return {
                'status': 'warning',
                'message': f'Insufficient data points to calculate changes for {symbol}.',
                'name': symbol, 'category': 'index',
                'latest_close': latest_close_val if pd.notna(latest_close_val) else None,
                'change': 0, 'change_percent': 0,
                'mini_chart_data': raw_mini_chart
            }
        except Exception as e:
            logger.error(f"Error processing display data for {symbol}: {e}", exc_info=True)
            raw_data_fallback = df[['time', 'close']].tail(30).to_dict(orient='records') if not df.empty else []
            return {
                'status': 'error',
                'message': f'Error processing display data for {symbol}: {str(e)}',
                'name': symbol, 'category': 'index', 'latest_close': None,
                'change': None, 'change_percent': None, 'mini_chart_data': raw_data_fallback
            }

    async def fetch_and_process_all_indices(self) -> Dict[str, Dict[str, any]]:
        if not self.INDEX_CONFIG:
            logger.warning("INDEX_CONFIG is empty. No indices to process.")
            return {}
        logger.info(f"Starting to fetch and process all configured indices: {list(self.INDEX_CONFIG.keys())}")
        processed_results: Dict[str, Dict[str, any]] = {}
        for index_symbol, config_details in self.INDEX_CONFIG.items():
            index_type_name = config_details.get('index_type')
            source_api = config_details.get('source', 'VCI')
            if not index_type_name:
                logger.error(f"Missing 'index_type' in config for {index_symbol}. Skipping.")
                processed_results[index_symbol] = {'status': 'error', 'message': 'Configuration error: missing index_type.'}
                continue
            logger.info(f"--- Processing index: {index_symbol} ---")
            try:
                df_all_data_for_index = self.get_and_update_index_data(index_symbol, index_type_name, source_api)
                display_data = self.process_index_data_for_display(df_all_data_for_index, index_symbol)
                processed_results[index_symbol] = display_data
                logger.info(f"Successfully processed data for {index_symbol}. Status: {display_data.get('status')}")
            except Exception as e:
                logger.exception(f"CRITICAL error while processing index {index_symbol}: {e}")
                processed_results[index_symbol] = {
                    'status': 'error',
                    'message': f'System error processing {index_symbol}: {str(e)}',
                    'name': index_symbol, 'category': 'index', 'latest_close': None,
                    'change': None, 'change_percent': None, 'mini_chart_data': []
                }
            logger.info(f"--- Finished processing index: {index_symbol} ---")
        logger.info(f"Completed fetching and processing for all {len(self.INDEX_CONFIG)} indices.")
        return processed_results

# ==== MARKET DATA SERVICE (from market_data_service.py) ====
class MarketDataService:
    def __init__(self):
        self.supabase: Client = get_supabase_client()
    def get_market_cap(
        self,
        line_item_id: int,
        year: int,
        quarter: str,
        min_stock_id: int,
        max_stock_id: int
    ) -> List[MarketCapItem]:
        try:
            response = self.supabase.table("financial_data") \
                .select("value, financial_reports!inner(stock_id, year, quarter, stocks!inner(symbol))") \
                .eq("line_item_id", line_item_id) \
                .eq("financial_reports.year", year) \
                .eq("financial_reports.quarter", quarter) \
                .gte("financial_reports.stock_id", min_stock_id) \
                .lte("financial_reports.stock_id", max_stock_id) \
                .execute()
            if response.data is None and response.error:
                print(f"Supabase Error: {response.error}")
                raise HTTPException(status_code=500, detail=f"Error fetching data from Supabase: {response.error.message}")
            processed_data: List[MarketCapItem] = []
            if response.data:
                for item in response.data:
                    report_info = item.get('financial_reports')
                    stock_info = report_info.get('stocks') if report_info else None
                    if stock_info and 'symbol' in stock_info and 'value' in item:
                        item_value = item['value']
                        if item_value is not None and item_value > 0:
                            processed_data.append(
                                MarketCapItem(symbol=stock_info['symbol'], value=item_value)
                            )
                    else:
                        print(f"Skipping item due to missing data: {item}")
            processed_data.sort(key=lambda x: x.value, reverse=True)
            return processed_data
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            print(f"An error occurred in MarketDataService: {e}")
            raise HTTPException(status_code=500, detail=f"An internal server error occurred in service: {str(e)}")
market_data_service = MarketDataService()
def get_market_data_service() -> MarketDataService:
    return market_data_service

# ==== NEWS SERVICE (from news_service.py) ====
def fetch_all_news() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    try:
        response = client.table("news").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching all news: {e}")
        return []
def fetch_news_by_id(news_id: int) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    try:
        response = client.table("news").select("*").eq("id", news_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching news by id {news_id}: {e}")
        return None 