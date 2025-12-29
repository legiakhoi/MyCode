import os
import sys
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
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }

def main():
    try:
        # Load environment variables
        config = load_environment_variables()
        
        # Import vanna here to avoid import errors if not installed
        try:
            from vanna.remote import VannaDefault
        except ImportError:
            logger.error("Vanna package is not installed. Please install it with: pip install vanna==0.7.9")
            print("Lỗi: Chưa cài đặt gói Vanna. Vui lòng cài đặt với lệnh: pip install vanna==0.7.9")
            return
        
        # Initialize Vanna with remote model
        # Note: You need to create an account at https://vanna.ai/account/profile to get your model name
        # For now, we'll use a demo model
        try:
            vn = VannaDefault(model='chinook', api_key=config['gemini_api_key'])
            logger.info("Vanna initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Vanna: {e}")
            print(f"Lỗi khi khởi tạo Vanna: {e}")
            print("Bạn cần tạo tài khoản tại https://vanna.ai/account/profile để lấy model name và API key")
            return
        
        # Connect to the database
        logger.info("Connecting to database...")
        vn.connect_to_postgres(
            host=config['host'],
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            port=int(config['port'])
        )
        logger.info("Database connection successful")
        
        # --- THỬ NGHIỆM ---
        print("Đang kết nối và học dữ liệu...")
        
        # Lệnh này sẽ quét DB và lưu kiến thức
        # Chỉ cần chạy lần đầu, các lần sau có thể comment lại dòng này
        try:
            vn.train()
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