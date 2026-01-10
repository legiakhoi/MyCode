import os
import pandas as pd
from sqlalchemy import create_engine, exc
from dotenv import load_dotenv
import logging
import sys

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
        'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 10)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30))
    }

def create_database_connection(config):
    """Create a database connection using the provided configuration."""
    db_uri = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            db_uri,
            pool_size=config['pool_size'],
            max_overflow=config['max_overflow'],
            pool_timeout=config['pool_timeout']
        )
        logger.info("Database engine created successfully")
        return engine
    except exc.SQLAlchemyError as e:
        logger.error(f"Error creating database engine: {e}")
        raise

def execute_query(engine, query, limit=5):
    """Execute a SQL query and return the results as a pandas DataFrame."""
    try:
        # Add LIMIT clause if not already present
        if 'limit' not in query.lower() and 'LIMIT' not in query:
            query = f"{query} LIMIT {limit}"
        
        # Execute query and load results into DataFrame
        df = pd.read_sql(query, engine)
        logger.info(f"Query executed successfully. Retrieved {len(df)} rows.")
        return df
    except exc.SQLAlchemyError as e:
        logger.error(f"Error executing query: {e}")
        raise

def save_to_excel(df, filename="ket_qua.xlsx"):
    """Save DataFrame to an Excel file."""
    try:
        df.to_excel(filename, index=False)
        logger.info(f"Data successfully saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to Excel: {e}")
        raise

def main():
    """Main function to connect to the database and retrieve data."""
    try:
        # Load environment variables
        config = load_environment_variables()
        
        # Create database connection
        engine = create_database_connection(config)
        
        # Execute query
        query = "SELECT * FROM tbl_documents"
        df = execute_query(engine, query)
        
        # Display results
        print("Kết nối THÀNH CÔNG! Dữ liệu mẫu:")
        print(df)
        
        # Save to Excel (uncomment to enable)
        save_to_excel(df)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    main()