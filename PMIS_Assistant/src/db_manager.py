import psycopg
from psycopg.rows import dict_row
from typing import Dict, List, Any, Optional, Tuple
import logging
from contextlib import contextmanager
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Quản lý kết nối và thao tác với cơ sở dữ liệu PostgreSQL"""
    
    def __init__(self):
        self.connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'dbname': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
        self.connection = None
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """Context manager để lấy cursor từ connection"""
        cursor = None
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg.connect(**self.connection_params)
                
            if dictionary:
                cursor = self.connection.cursor(row_factory=dict_row)
            else:
                cursor = self.connection.cursor()
                
            yield cursor
            self.connection.commit()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Kiểm tra kết nối đến cơ sở dữ liệu"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Lấy schema của một bảng cụ thể"""
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (table_name,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return []
    
    def get_main_tables_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Lấy thông tin từ các bảng chính để làm context cho AI"""
        result = {}
        
        # Lấy thông tin từ bảng DuAn
        result['projects'] = self.get_table_data('"DuAn"', ['"ID"', '"MaDuAn"', '"TenDuAn"'])
        
        # Lấy thông tin từ bảng PhongBan
        result['departments'] = self.get_table_data('"PhongBan"', ['"ID"', '"MaPhongBan"', '"TenPhongBan"'])
        
        # Lấy thông tin từ bảng CongViec
        result['tasks'] = self.get_table_data('"CongViec"', ['"ID"', '"TenCongViec"', '"DuAn_ID"'])
        
        # Lấy thông tin từ bảng VanDe
        result['issues'] = self.get_table_data('"VanDe"', ['"ID"', '"MoTaVanDe"', '"DuAn_ID"'])
        
        # Lấy thông tin từ bảng TienTrinhXuLy
        result['progress'] = self.get_table_data('"TienTrinhXuLy"', ['"ID"', '"CongViec_ID"', '"TinhTrangThucHien"'])
        
        return result
    
    def get_table_data(self, table_name: str, columns: List[str] = None) -> List[Dict[str, Any]]:
        """Lấy dữ liệu từ một bảng cụ thể"""
        if columns is None:
            # Lấy tất cả các cột trừ các cột hệ thống
            schema = self.get_table_schema(table_name)
            columns = [col['column_name'] for col in schema 
                      if col['column_name'] not in ['is_deleted', 'last_updated']]
        
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table_name} WHERE is_deleted = FALSE OR is_deleted IS NULL"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting data from table {table_name}: {e}")
            return []
    
    def get_all_tables(self) -> List[str]:
        """Lấy danh sách tất cả các bảng trong database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Lấy danh sách các cột của một bảng"""
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (table_name,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {e}")
            return []
    
    def insert_document(self, table_name: str, data: Dict[str, Any]) -> int:
        """Chèn dữ liệu vào bảng cụ thể và trả về ID của bản ghi mới"""
        # Lọc ra các cột có trong bảng
        table_columns = [col['column_name'] for col in self.get_table_columns(table_name)]
        filtered_data = {k: v for k, v in data.items() if k in table_columns}
        
        if not filtered_data:
            raise ValueError(f"No valid columns found for table {table_name}")
        
        columns = list(filtered_data.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        values = list(filtered_data.values())
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING ID"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error inserting into table {table_name}: {e}")
            raise
    
    def insert_into_documents_table(self, document_data: Dict[str, Any]) -> int:
        """Chèn dữ liệu vào bảng tbl_documents"""
        table_name = 'tbl_documents'
        return self.insert_document(table_name, document_data)
    
    def log_ai_activity(self, filename: str, ai_response: str, status: str) -> int:
        """Ghi log hoạt động của AI vào bảng gemini_automation_log"""
        query = """
        INSERT INTO gemini_automation_log (filename, ai_response, status, processed_at)
        VALUES (%s, %s, %s, NOW())
        RETURNING id
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (filename, ai_response, status))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error logging AI activity: {e}")
            raise
    
    def search_data(self, table_name: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tìm kiếm dữ liệu trong bảng với các bộ lọc"""
        if not filters:
            return self.get_table_data(table_name)
        
        # Xây dựng câu query động
        where_conditions = []
        values = []
        
        for column, value in filters.items():
            if value and value.strip():
                where_conditions.append(f"{column} ILIKE %s")
                values.append(f"%{value.strip()}%")
        
        if not where_conditions:
            return self.get_table_data(table_name)
        
        where_clause = " AND ".join(where_conditions)
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, values)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error searching in table {table_name}: {e}")
            return []
    
    def close(self):
        """Đóng kết nối đến database"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Database connection closed")