import os
import shutil
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

class FileManager:
    """Quản lý file và thư mục cho PMIS Assistant"""
    
    def __init__(self):
        self.default_base_path = config.DEFAULT_DOCUMENT_PATH
        
    def suggest_filename(self, analysis_result: Dict[str, Any], original_filename: str = "") -> str:
        """
        Đề xuất tên file dựa trên kết quả phân tích của AI
        
        Args:
            analysis_result: Kết quả phân tích từ AI
            original_filename: Tên file gốc (nếu có)
            
        Returns:
            Tên file theo quy chuẩn YYYYMMDD_MaDuAn_MaPhongBan_Loai_MoTaNgan.ext
        """
        # Nếu AI đã đề xuất tên file, sử dụng nó
        suggested = analysis_result.get("suggested_filename", "")
        if suggested:
            return suggested
        
        # Nếu không, tự tạo tên file dựa trên kết quả mapping
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Lấy mã dự án
        project_mapping = analysis_result.get("mapping_results", {}).get("DuAn", {})
        if project_mapping.get("matched", False):
            project_code = project_mapping.get("project_code", "UNKNOWN")
        else:
            project_code = "UNKNOWN"
        
        # Lấy mã phòng ban
        dept_mapping = analysis_result.get("mapping_results", {}).get("PhongBan", {})
        if dept_mapping.get("matched", False):
            dept_code = dept_mapping.get("department_code", "UNKNOWN")
        else:
            dept_code = "UNKNOWN"
        
        # Lấy loại tài liệu
        doc_info = analysis_result.get("document_info", {})
        doc_type = doc_info.get("document_type", "DOC")
        
        # Lấy mô tả ngắn
        summary = analysis_result.get("summary", "")
        if summary:
            # Lấy 3 từ đầu của summary và làm sạch
            words = summary.split()[:3]
            desc = "_".join([word.strip(",.") for word in words])
            # Loại bỏ ký tự đặc biệt và giới hạn độ dài
            import re
            desc = re.sub(r'[^\w\s]', '', desc)
            desc = re.sub(r'\s+', '_', desc)
            desc = desc[:20] if len(desc) > 20 else desc
        else:
            desc = "document"
        
        # Lấy extension từ file gốc nếu có
        if original_filename:
            _, ext = os.path.splitext(original_filename)
        else:
            ext = ".pdf"  # Mặc định là PDF
        
        return f"{date_str}_{project_code}_{dept_code}_{doc_type}_{desc}{ext}"
    
    def suggest_destination(self, analysis_result: Dict[str, Any]) -> str:
        """
        Đề xuất vị trí lưu file dựa trên kết quả phân tích
        
        Args:
            analysis_result: Kết quả phân tích từ AI
            
        Returns:
            Đường dẫn thư mục đề xuất
        """
        # Nếu AI đã đề xuất vị trí, sử dụng nó
        suggested = analysis_result.get("suggested_destination", "")
        if suggested:
            return suggested
        
        # Nếu không, tự tạo đường dẫn dựa trên kết quả mapping
        base_path = self.default_base_path
        
        # Lấy thông tin dự án
        project_mapping = analysis_result.get("mapping_results", {}).get("DuAn", {})
        if project_mapping.get("matched", False):
            project_code = project_mapping.get("project_code", "UNKNOWN")
            project_name = project_mapping.get("project_name", "Unknown Project")
            # Làm sạch tên dự án để làm tên thư mục
            import re
            project_folder = re.sub(r'[^\w\s-]', '', project_name).strip()
            project_folder = re.sub(r'\s+', '_', project_folder)
            base_path = os.path.join(base_path, f"{project_code}_{project_folder}")
        
        # Lấy loại tài liệu
        doc_info = analysis_result.get("document_info", {})
        doc_type_name = doc_info.get("document_type_name", "TaiLieu")
        if doc_type_name:
            # Làm sạch tên loại tài liệu
            import re
            doc_type_folder = re.sub(r'[^\w\s-]', '', doc_type_name).strip()
            doc_type_folder = re.sub(r'\s+', '_', doc_type_folder)
            base_path = os.path.join(base_path, doc_type_folder)
        
        # Thêm thư mục theo năm tháng
        now = datetime.now()
        year_month = now.strftime("%Y_%m")
        base_path = os.path.join(base_path, year_month)
        
        return base_path
    
    def create_directory_if_not_exists(self, path: str) -> bool:
        """
        Tạo thư mục nếu chưa tồn tại
        
        Args:
            path: Đường dẫn thư mục cần tạo
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.info(f"Created directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def move_file(self, source_path: str, destination_dir: str, new_filename: str) -> Tuple[bool, str]:
        """
        Di chuyển file đến vị trí mới với tên mới
        
        Args:
            source_path: Đường dẫn file nguồn
            destination_dir: Thư mục đích
            new_filename: Tên file mới
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Kiểm tra file nguồn có tồn tại không
            if not os.path.exists(source_path):
                return False, f"File nguồn không tồn tại: {source_path}"
            
            # Tạo thư mục đích nếu chưa tồn tại
            if not self.create_directory_if_not_exists(destination_dir):
                return False, f"Không thể tạo thư mục đích: {destination_dir}"
            
            # Đường dẫn file đích
            destination_path = os.path.join(destination_dir, new_filename)
            
            # Nếu file đích đã tồn tại, thêm timestamp vào tên file
            if os.path.exists(destination_path):
                name, ext = os.path.splitext(new_filename)
                timestamp = datetime.now().strftime("%H%M%S")
                new_filename = f"{name}_{timestamp}{ext}"
                destination_path = os.path.join(destination_dir, new_filename)
            
            # Di chuyển file
            shutil.move(source_path, destination_path)
            
            logger.info(f"Moved file from {source_path} to {destination_path}")
            return True, destination_path
            
        except Exception as e:
            logger.error(f"Failed to move file {source_path}: {e}")
            return False, f"Lỗi khi di chuyển file: {str(e)}"
    
    def copy_file(self, source_path: str, destination_dir: str, new_filename: str) -> Tuple[bool, str]:
        """
        Sao chép file đến vị trí mới với tên mới
        
        Args:
            source_path: Đường dẫn file nguồn
            destination_dir: Thư mục đích
            new_filename: Tên file mới
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Kiểm tra file nguồn có tồn tại không
            if not os.path.exists(source_path):
                return False, f"File nguồn không tồn tại: {source_path}"
            
            # Tạo thư mục đích nếu chưa tồn tại
            if not self.create_directory_if_not_exists(destination_dir):
                return False, f"Không thể tạo thư mục đích: {destination_dir}"
            
            # Đường dẫn file đích
            destination_path = os.path.join(destination_dir, new_filename)
            
            # Nếu file đích đã tồn tại, thêm timestamp vào tên file
            if os.path.exists(destination_path):
                name, ext = os.path.splitext(new_filename)
                timestamp = datetime.now().strftime("%H%M%S")
                new_filename = f"{name}_{timestamp}{ext}"
                destination_path = os.path.join(destination_dir, new_filename)
            
            # Sao chép file
            shutil.copy2(source_path, destination_path)
            
            logger.info(f"Copied file from {source_path} to {destination_path}")
            return True, destination_path
            
        except Exception as e:
            logger.error(f"Failed to copy file {source_path}: {e}")
            return False, f"Lỗi khi sao chép file: {str(e)}"
    
    def save_text_to_file(self, text_content: str, destination_dir: str, filename: str) -> Tuple[bool, str]:
        """
        Lưu nội dung văn bản vào file
        
        Args:
            text_content: Nội dung văn bản cần lưu
            destination_dir: Thư mục đích
            filename: Tên file
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Tạo thư mục đích nếu chưa tồn tại
            if not self.create_directory_if_not_exists(destination_dir):
                return False, f"Không thể tạo thư mục đích: {destination_dir}"
            
            # Đường dẫn file đích
            destination_path = os.path.join(destination_dir, filename)
            
            # Nếu file đích đã tồn tại, thêm timestamp vào tên file
            if os.path.exists(destination_path):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"{name}_{timestamp}{ext}"
                destination_path = os.path.join(destination_dir, filename)
            
            # Lưu nội dung vào file
            with open(destination_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"Saved text to file: {destination_path}")
            return True, destination_path
            
        except Exception as e:
            logger.error(f"Failed to save text to file: {e}")
            return False, f"Lỗi khi lưu file: {str(e)}"
    
    def get_directory_tree(self, root_path: str = None, max_depth: int = 3) -> Dict[str, Any]:
        """
        Lấy cấu trúc cây thư mục
        
        Args:
            root_path: Đường dẫn thư mục gốc
            max_depth: Độ sâu tối đa của cây
            
        Returns:
            Dict chứa cấu trúc cây thư mục
        """
        if root_path is None:
            root_path = self.default_base_path
        
        if not os.path.exists(root_path):
            return {"error": f"Thư mục không tồn tại: {root_path}"}
        
        try:
            result = {
                "name": os.path.basename(root_path),
                "path": root_path,
                "type": "directory",
                "children": []
            }
            
            self._build_directory_tree(root_path, result["children"], max_depth, 0)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get directory tree for {root_path}: {e}")
            return {"error": f"Lỗi khi đọc cấu trúc thư mục: {str(e)}"}
    
    def _build_directory_tree(self, path: str, children_list: list, max_depth: int, current_depth: int):
        """Hàm đệ quy để xây dựng cấu trúc cây thư mục"""
        if current_depth >= max_depth:
            return
        
        try:
            # Lấy danh sách các thư mục con và file
            items = []
            try:
                items = os.listdir(path)
            except PermissionError:
                # Không có quyền truy cập
                return
            
            # Sắp xếp theo thứ tự: thư mục trước, file sau
            directories = []
            files = []
            
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
            
            directories.sort()
            files.sort()
            
            # Xử lý thư mục
            for directory in directories:
                dir_path = os.path.join(path, directory)
                dir_node = {
                    "name": directory,
                    "path": dir_path,
                    "type": "directory",
                    "children": []
                }
                children_list.append(dir_node)
                
                # Đệ quy để lấy thư mục con
                self._build_directory_tree(dir_path, dir_node["children"], max_depth, current_depth + 1)
            
            # Xử lý file
            for file in files:
                file_path = os.path.join(path, file)
                file_node = {
                    "name": file,
                    "path": file_path,
                    "type": "file"
                }
                children_list.append(file_node)
                
        except Exception as e:
            logger.error(f"Error building directory tree for {path}: {e}")
    
    def validate_filename(self, filename: str) -> Tuple[bool, str]:
        """
        Kiểm tra tính hợp lệ của tên file
        
        Args:
            filename: Tên file cần kiểm tra
            
        Returns:
            Tuple (is_valid: bool, error_message: str)
        """
        if not filename:
            return False, "Tên file không được để trống"
        
        # Kiểm tra các ký tự không hợp lệ trong Windows
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in filename:
                return False, f"Tên file không được chứa ký tự: {char}"
        
        # Kiểm tra độ dài
        if len(filename) > 255:
            return False, "Tên file quá dài (tối đa 255 ký tự)"
        
        # Kiểm tra tên file dành riêng
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            return False, f"Tên file '{filename}' là tên dành riêng và không được sử dụng"
        
        return True, ""
    
    def clean_filename(self, filename: str) -> str:
        """
        Làm sạch tên file bằng cách thay thế các ký tự không hợp lệ
        
        Args:
            filename: Tên file cần làm sạch
            
        Returns:
            Tên file đã được làm sạch
        """
        import re
        
        # Thay thế các ký tự không hợp lệ
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Loại bỏ các ký tự control
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Loại bỏ khoảng trắng ở đầu và cuối
        filename = filename.strip()
        
        # Giới hạn độ dài
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            max_name_length = 255 - len(ext)
            filename = name[:max_name_length] + ext
        
        return filename