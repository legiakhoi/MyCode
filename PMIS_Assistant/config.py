import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pmis_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2000"))

# Application Configuration
APP_NAME = os.getenv("APP_NAME", "PMIS Assistant")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_DOCUMENT_PATH = os.getenv("DEFAULT_DOCUMENT_PATH", os.path.join(os.path.expanduser("~"), "Documents/PMIS_Documents"))

# Hotkey Configuration
HOTKEY_COMBINATION = "ctrl+c"

# UI Configuration
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# File type mapping for naming convention
DOCUMENT_TYPES = {
    "Quyết định": "QD",
    "Báo cáo": "BC",
    "Công văn": "CV",
    "Thông báo": "TB",
    "Tổng trình": "TTr",
    "Hợp đồng": "HD",
    "Biên bản": "BB",
    "Kế hoạch": "KH",
    "Đề án": "DA",
    "Tờ trình": "TT"
}

# Database tables to consider for mapping
MAIN_TABLES = [
    "DuAn",
    "CongViec", 
    "VanDe",
    "TienTrinhXuLy",
    "PhongBan",
    "HopDong",
    "VanBanPhapLy",
    "GoiThau"
]

# Validate required environment variables
def validate_config():
    """Validate that required environment variables are set"""
    missing_vars = []
    
    if not DB_PASSWORD:
        missing_vars.append("DB_PASSWORD")
    
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True