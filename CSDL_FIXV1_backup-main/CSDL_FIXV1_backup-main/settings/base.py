from typing import Any, Dict

class BaseConfig:
    """Cấu hình cơ sở cho ứng dụng"""
    
    # Cấu hình chung
    DEBUG: bool = False
    ENV: str = 'production'
    
    # Cấu hình cơ sở dữ liệu
    DATABASE_URI: str = 'sqlite:///finance.db'
    
    def get_settings(self) -> Dict[str, Any]:
        """Trả về tất cả cài đặt dưới dạng dictionary"""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}
    