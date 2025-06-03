from .base_config import BaseConfig
from .supabase_settings import SupabaseSettings

# Tạo instance mặc định cho cấu hình
base_settings = BaseConfig()
supabase_settings = SupabaseSettings()

__all__ = [
    'BaseConfig',
    'SupabaseSettings',
    'base_settings', 
    'supabase_settings'
]