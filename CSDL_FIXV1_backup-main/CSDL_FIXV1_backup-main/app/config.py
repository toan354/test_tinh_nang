import os
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from supabase import create_client, Client
from dotenv import load_dotenv

# Load .env nếu có
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://gqudofrvqpesiyibtgnt.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    APP_TITLE: str = "Financial Data & Analysis API"
    APP_DESCRIPTION: str = "API hợp nhất cung cấp dữ liệu tài chính, thị trường chứng khoán, tin tức và các phân tích."
    APP_VERSION: str = "2.0.3"
    DEBUG_MODE: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://127.0.0.1",
        "null",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    INDEX_CONFIG: Dict[str, Dict[str, Any]] = {
        'VNINDEX': {'index_type': 'VN', 'index_type_id': None, 'source': 'VCI', 'table': 'index_history', 'default_start_date': '2020-01-01'},
        'HNXINDEX': {'index_type': 'HNX', 'index_type_id': None, 'source': 'VCI', 'table': 'index_history', 'default_start_date': '2020-01-01'},
        'UPCOMINDEX': {'index_type': 'UPCOM', 'index_type_id': None, 'source': 'VCI', 'table': 'index_history', 'default_start_date': '2020-01-01'}
    }

    WEBSOCKET_STOCK_INTERVAL_SECONDS: int = 10
    DEFAULT_LINE_ITEM_ID_TONG_NGUON_VON: int = 88
    DEFAULT_YEAR_TONG_NGUON_VON: int = 2024
    DEFAULT_QUARTER_TONG_NGUON_VON: str = "Q4"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

@lru_cache()
def get_settings() -> Settings:
    current_settings = Settings()
    logging.getLogger().setLevel(current_settings.LOG_LEVEL.upper())
    return current_settings

@lru_cache()
def get_supabase_client() -> Client:
    current_app_settings = get_settings()
    if not current_app_settings.SUPABASE_URL or not current_app_settings.SUPABASE_KEY:
        logger.error("CRITICAL: Supabase URL or Key is missing in loaded settings. Cannot initialize client.")
        raise ValueError("Supabase URL or Key is missing in settings. Cannot initialize Supabase client.")
    try:
        supabase: Client = create_client(current_app_settings.SUPABASE_URL, current_app_settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
        return supabase
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize Supabase client: {e}", exc_info=True)
        raise RuntimeError(f"Supabase client initialization failed: {e}") from e

settings: Settings = get_settings() 