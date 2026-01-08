import os
import tempfile
import shutil
import time
from PIL import Image, ImageGrab
import win32clipboard
import win32con
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ClipboardHandler:
    """Xử lý các loại dữ liệu từ clipboard Windows"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def get_clipboard_data(self) -> Dict[str, Any]:
        """
        Lấy dữ liệu từ clipboard và trả về thông tin về loại dữ liệu và nội dung
        
        Returns:
            Dict chứa thông tin về dữ liệu clipboard:
            - type: 'text', 'image', 'file', or 'empty'
            - content: nội dung dữ liệu
            - metadata: thông tin bổ sung
        """
        try:
            # Kiểm tra xem có dữ liệu trong clipboard không
            if not self._has_clipboard_data():
                return {"type": "empty", "content": None, "metadata": {}}
            
            # Thử lấy dữ liệu file trước (độ ưu tiên cao nhất)
            file_data = self._get_file_data()
            if file_data:
                return file_data
            
            # Thử lấy dữ liệu ảnh
            image_data = self._get_image_data()
            if image_data:
                return image_data
            
            # Thử lấy dữ liệu text
            text_data = self._get_text_data()
            if text_data:
                return text_data
            
            # Nếu không có loại dữ liệu nào được hỗ trợ
            return {"type": "unsupported", "content": None, "metadata": {}}
            
        except Exception as e:
            logger.error(f"Error getting clipboard data: {e}")
            return {"type": "error", "content": None, "metadata": {"error": str(e)}}
    
    def _has_clipboard_data(self) -> bool:
        """Kiểm tra xem có dữ liệu trong clipboard không"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(0.1)  # Small delay before accessing clipboard
                win32clipboard.OpenClipboard()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error opening clipboard after {max_retries} attempts: {e}")
                    return False
                time.sleep(0.2)
                continue
        
        try:
            # Kiểm tra các format phổ biến
            formats = []
            format_id = 0
            while True:
                format_id = win32clipboard.EnumClipboardFormats(format_id)
                if format_id == 0:
                    break
                formats.append(format_id)
            
            # Kiểm tra xem có format nào được hỗ trợ không
            has_text = win32con.CF_TEXT in formats
            has_unicode = win32con.CF_UNICODETEXT in formats
            has_hdrop = win32con.CF_HDROP in formats
            has_dib = win32con.CF_DIB in formats
            
            result = has_text or has_unicode or has_hdrop or has_dib
            win32clipboard.CloseClipboard()
            return result
        except Exception as e:
            logger.error(f"Error checking clipboard data: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return False
    
    def _get_text_data(self) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu văn bản từ clipboard"""
        try:
            win32clipboard.OpenClipboard()
            
            # Thử lấy text unicode trước
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                
                return {
                    "type": "text",
                    "content": data,
                    "metadata": {
                        "length": len(data),
                        "encoding": "unicode",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            # Thử lấy text ANSI
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                win32clipboard.CloseClipboard()
                
                # Giải mã từ bytes sang string
                try:
                    text_data = data.decode('utf-8')
                except UnicodeDecodeError:
                    text_data = data.decode('latin-1', errors='ignore')
                
                return {
                    "type": "text",
                    "content": text_data,
                    "metadata": {
                        "length": len(text_data),
                        "encoding": "ansi",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            win32clipboard.CloseClipboard()
            return None
            
        except Exception as e:
            logger.error(f"Error getting text data: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    
    def _get_image_data(self) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu ảnh từ clipboard"""
        try:
            # Sử dụng PIL ImageGrab để lấy ảnh
            image = ImageGrab.grabclipboard()
            
            if isinstance(image, Image.Image):
                # Lưu ảnh tạm thời
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"clipboard_image_{timestamp}.png"
                temp_path = os.path.join(self.temp_dir, temp_filename)
                
                # Lưu ảnh với độ phân giải tốt
                image.save(temp_path, "PNG", optimize=True)
                
                return {
                    "type": "image",
                    "content": temp_path,
                    "metadata": {
                        "format": image.format,
                        "size": image.size,
                        "mode": image.mode,
                        "temp_path": temp_path,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting image data: {e}")
            return None
    
    def _get_file_data(self) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu file từ clipboard"""
        try:
            win32clipboard.OpenClipboard()
            
            # Kiểm tra format file (CF_HDROP)
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                data = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                win32clipboard.CloseClipboard()
                
                # CF_HDROP trả về một tuple chứa các đường dẫn file
                if data and len(data) > 0:
                    file_paths = list(data)
                    
                    # Nếu chỉ có một file, xử lý file đó
                    if len(file_paths) == 1:
                        file_path = file_paths[0]
                        
                        if os.path.exists(file_path):
                            file_info = self._get_file_info(file_path)
                            
                            return {
                                "type": "file",
                                "content": file_path,
                                "metadata": {
                                    **file_info,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }
                    else:
                        # Nếu có nhiều file, trả về danh sách
                        files_info = []
                        for path in file_paths:
                            if os.path.exists(path):
                                files_info.append(self._get_file_info(path))
                        
                        return {
                            "type": "files",
                            "content": file_paths,
                            "metadata": {
                                "count": len(file_paths),
                                "files": files_info,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
            
            win32clipboard.CloseClipboard()
            return None
            
        except Exception as e:
            logger.error(f"Error getting file data: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Lấy thông tin chi tiết về file"""
        try:
            stat = os.stat(file_path)
            
            # Xác định loại file dựa trên extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            file_type = "unknown"
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                file_type = "text"
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                file_type = "image"
            elif ext in ['.pdf']:
                file_type = "pdf"
            elif ext in ['.doc', '.docx']:
                file_type = "word"
            elif ext in ['.xls', '.xlsx']:
                file_type = "excel"
            elif ext in ['.ppt', '.pptx']:
                file_type = "powerpoint"
            
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "extension": ext,
                "type": file_type,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "error": str(e)
            }
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """Đọc nội dung file (chỉ cho các file text-based)"""
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Xử lý các loại file text-based
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # Xử lý file PDF
            elif ext == '.pdf':
                return self._read_pdf_content(file_path)
            
            # Xử lý file Word
            elif ext in ['.doc', '.docx']:
                return self._read_word_content(file_path)
            
            else:
                logger.warning(f"Unsupported file type for reading: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading file content from {file_path}: {e}")
            return None
    
    def _read_pdf_content(self, file_path: str) -> Optional[str]:
        """Đọc nội dung từ file PDF"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        except ImportError:
            logger.warning("PyPDF2 not installed, cannot read PDF content")
            return None
        except Exception as e:
            logger.error(f"Error reading PDF content: {e}")
            return None
    
    def _read_word_content(self, file_path: str) -> Optional[str]:
        """Đọc nội dung từ file Word"""
        try:
            import docx
            
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
                
        except ImportError:
            logger.warning("python-docx not installed, cannot read Word content")
            return None
        except Exception as e:
            logger.error(f"Error reading Word content: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Dọn dẹp các file tạm thời đã tạo"""
        try:
            temp_files = [f for f in os.listdir(self.temp_dir) 
                         if f.startswith("clipboard_image_") and f.endswith(".png")]
            
            for temp_file in temp_files:
                temp_path = os.path.join(self.temp_dir, temp_file)
                try:
                    os.remove(temp_path)
                    logger.debug(f"Removed temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")