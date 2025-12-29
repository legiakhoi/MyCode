import os
import sys
from vanna.google import GoogleGeminiChat
from vanna.chromadb import ChromaDB_VectorStore
from dotenv import load_dotenv
import logging

# Configure console encoding for Windows to handle Vietnamese characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment_variables():
    """Load environment variables from .env file."""
    load_dotenv()  # Load environment variables from .env file
    
    # Check if required environment variables are set
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'gemini_model': os.getenv('GEMINI_MODEL', 'gemini-flash-latest')
    }

# Định nghĩa lớp Vanna chạy Local + Gemini
class MyVanna(ChromaDB_VectorStore, GoogleGeminiChat):
    def __init__(self, config=None):
        try:
            # Khởi tạo lưu trữ local (Sẽ tạo thư mục 'vanna_chromadb' ngay tại đây)
            ChromaDB_VectorStore.__init__(self, config=config)
            logger.info("ChromaDB Vector Store initialized successfully")
            
            # Khởi tạo não bộ Gemini
            GoogleGeminiChat.__init__(self, config=config)
            logger.info("Google Gemini Chat initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Vanna: {e}")
            raise

def main():
    try:
        # Load environment variables
        config = load_environment_variables()
        
        # Prepare database configuration
        db_config = {
            'host': config['host'],
            'port': int(config['port']),
            'dbname': config['dbname'],
            'user': config['user'],
            'password': config['password']
        }
        
        # Prepare Gemini configuration
        gemini_config = {
            'api_key': config['gemini_api_key'],
            'model': config['gemini_model']
        }
        
        # Khởi tạo đối tượng
        logger.info("Initializing Vanna...")
        vn = MyVanna(config=gemini_config)
        
        # Kết nối Database
        logger.info("Connecting to database...")
        vn.connect_to_postgres(**db_config)
        logger.info("Database connection successful")
        
        # --- THỬ NGHIỆM ---
        print("Đang kết nối và học dữ liệu...")
        
        # Lệnh này sẽ quét DB và lưu kiến thức vào thư mục máy tính của bạn
        # Chỉ cần chạy lần đầu, các lần sau có thể comment lại dòng này
        try:
            vn.train(db_conn=vn.db_conn)
            logger.info("Database training completed successfully")
        except Exception as e:
            logger.warning(f"Error during training: {e}")
            print(f"Cảnh báo: Lỗi khi học dữ liệu: {e}")
            print("Tiếp tục với dữ liệu đã học trước đó...")
        
        # Hỏi thử
        cau_hoi = "Liệt kê 5 văn bản mới nhất"
        logger.info(f"Generating SQL for question: {cau_hoi}")
        
        try:
            sql = vn.generate_sql(cau_hoi)
            print(f"\nCâu hỏi: {cau_hoi}")
            print(f"SQL sinh ra: \n{sql}")
            
            # Chạy SQL lấy kết quả
            logger.info("Executing generated SQL...")
            df = vn.run_sql(sql)
            print("\nKết quả:")
            print(df)
            
        except Exception as e:
            logger.error(f"Error generating or executing SQL: {e}")
            print(f"Lỗi khi sinh hoặc thực thi SQL: {e}")
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Lỗi cấu hình: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    main()