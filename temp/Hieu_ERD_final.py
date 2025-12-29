import os
import sys
import pandas as pd
from sqlalchemy import create_engine
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
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
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
        'gemini_api_key': os.getenv('GEMINI_API_KEY', '')  # Optional for now
    }

def create_database_connection(config):
    """Create a database connection using the provided configuration."""
    db_uri = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"
    
    try:
        engine = create_engine(db_uri)
        logger.info("Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error creating database engine: {e}")
        raise

def execute_query(engine, query):
    """Execute a SQL query and return the results as a pandas DataFrame."""
    try:
        df = pd.read_sql(query, engine)
        logger.info(f"Query executed successfully. Retrieved {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

def main():
    """Main function to connect to the database and retrieve data."""
    try:
        # Load environment variables
        config = load_environment_variables()
        
        # Create database connection
        engine = create_database_connection(config)
        
        # Execute a simple query to test the connection
        query = "SELECT * FROM tbl_documents LIMIT 5;"
        df = execute_query(engine, query)
        
        # Display results
        print("Kết nối THÀNH CÔNG! Dữ liệu mẫu:")
        print(df)
        
        # Note about Vanna integration
        print("\nGhi chú về Vanna:")
        print("Để sử dụng tính năng AI của Vanna, bạn cần:")
        print("1. Tạo tài khoản tại https://vanna.ai/account/profile")
        print("2. Lấy API key và model name từ tài khoản của bạn")
        print("3. Cập nhật file .env với thông tin này")
        print("4. Sử dụng mã Vanna như trong file Hieu_ERD_simplified.py")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Lỗi cấu hình: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    main()