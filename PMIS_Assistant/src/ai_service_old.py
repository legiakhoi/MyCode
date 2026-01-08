import os
import json
import requests
import logging
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

class AIService:
    """Dịch vụ AI tích hợp với Gemini API để phân tích tài liệu"""
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self.temperature = config.GEMINI_TEMPERATURE
        self.max_tokens = config.GEMINI_MAX_TOKENS
        
        if not self.api_key:
            raise ValueError("Gemini API key is not configured")
    
    def analyze_clipboard_data(self, data: Dict[str, Any], db_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân tích dữ liệu từ clipboard và mapping với CSDL
        
        Args:
            data: Dữ liệu từ clipboard (text, image, file)
            db_context: Context từ CSDL (danh sách dự án, công việc, phòng ban, etc.)
            
        Returns:
            Dict chứa kết quả phân tích
        """
        try:
            # Lấy nội dung văn bản để phân tích
            text_content = self._extract_text_content(data)
            
            if not text_content or len(text_content.strip()) < 10:
                return self._get_default_result("Nội dung quá ngắn để phân tích")
            
            # Chuẩn bị prompt cho Gemini
            system_prompt = self._build_system_prompt(db_context)
            user_prompt = self._build_user_prompt(text_content, data)
            
            # Gọi API Gemini
            response = self._call_gemini_api(system_prompt, user_prompt)
            
            # Xử lý kết quả
            try:
                # Try to extract JSON from the response
                # Gemini might wrap JSON in markdown code blocks
                if "```json" in response:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    json_str = response[start:end].strip()
                elif "```" in response:
                    start = response.find("```") + 3
                    end = response.find("```", start)
                    json_str = response[start:end].strip()
                else:
                    json_str = response.strip()
                
                result = json.loads(json_str)
                return self._format_analysis_result(result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Response was: {response}")
                return self._get_default_result("Không thể phân tích kết quả từ AI")
                
        except ModuleNotFoundError as e:
            logger.error(f"Missing required module: {e}")
            return self._get_default_result("Thiếu thư viện cần thiết. Vui lòng cài đặt: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Error analyzing clipboard data: {e}")
            return self._get_default_result(f"Lỗi khi phân tích: {str(e)}")
    
    def _extract_text_content(self, data: Dict[str, Any]) -> str:
        """Trích xuất nội dung văn bản từ dữ liệu clipboard"""
        data_type = data.get("type", "")
        
        if data_type == "text":
            return data.get("content", "")
        elif data_type == "file":
            # Đọc nội dung file nếu là file text-based
            from .clipboard_handler import ClipboardHandler
            handler = ClipboardHandler()
            return handler.read_file_content(data.get("content", "")) or ""
        elif data_type == "image":
            # Sử dụng OCR để trích xuất text từ ảnh
            return self._extract_text_from_image(data.get("content", ""))
        else:
            return ""
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Trích xuất text từ ảnh sử dụng OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            # Mở ảnh và trích xuất text
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='vie+eng')
            return text
            
        except ImportError:
            logger.warning("pytesseract not installed, cannot extract text from image")
            return "[Không thể trích xuất text từ ảnh - cần cài đặt pytesseract]"
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return f"[Lỗi khi trích xuất text từ ảnh: {str(e)}]"
    
    def _build_system_prompt(self, db_context: Dict[str, Any]) -> str:
        """Xây dựng system prompt với context từ CSDL"""
        projects = db_context.get('projects', [])
        departments = db_context.get('departments', [])
        tasks = db_context.get('tasks', [])
        issues = db_context.get('issues', [])
        
        projects_info = "\n".join([f"- ID: {p['ID']}, Mã: {p['MaDuAn']}, Tên: {p['TenDuAn']}" for p in projects])
        departments_info = "\n".join([f"- ID: {d['ID']}, Mã: {d['MaPhongBan']}, Tên: {d['TenPhongBan']}" for d in departments])
        tasks_info = "\n".join([f"- ID: {t['ID']}, Tên: {t['TenCongViec']}, Dự án: {t['DuAn_ID']}" for t in tasks])
        issues_info = "\n".join([f"- ID: {i['ID']}, Mô tả: {i['MoTaVanDe']}, Dự án: {i['DuAn_ID']}" for i in issues])
        
        return f"""
Bạn là một trợ lý AI chuyên phân tích tài liệu dự án xây dựng. Hãy phân tích văn bản và mapping với các thực thể trong CSDL sau:

DANH SÁCH DỰ ÁN:
{projects_info}

DANH SÁCH PHÒNG BAN:
{departments_info}

DANH SÁCH CÔNG VIỆC:
{tasks_info}

DANH SÁCH VẤN ĐỀ:
{issues_info}

Hãy xác định văn bản liên quan đến thực thể nào trong danh sách trên và trả về kết quả với độ tin cậy (confidence score từ 0.0 đến 1.0).

Quy tắc đặt tên file: YYYYMMDD_MaDuAn_MaPhongBan_Loai_MoTaNgan.ext
Trong đó:
- YYYYMMDD: Ngày hiện tại ({datetime.now().strftime('%Y%m%d')})
- MaDuAn: Mã dự án từ CSDL
- MaPhongBan: Mã phòng ban từ CSDL
- Loai: Loại tài liệu (BC: Báo cáo, QD: Quyết định, CV: Công văn, TB: Thông báo, TTr: Tổng trình, HD: Hợp đồng, BB: Biên bản, KH: Kế hoạch, DA: Đề án, TT: Tờ trình)
- MoTaNgan: Tên file ngắn gọn về nội dung (không dấu, không quá 30 ký tự)
- ext: Phần mở rộng file

Trả về kết quả dưới dạng JSON với cấu trúc sau:
{{
  "summary": "Tóm tắt nội dung chính trong 2-3 câu",
  "mapping_results": {{
    "DuAn": {{"matched": true/false, "project_id": ID, "project_code": "Mã dự án", "project_name": "Tên dự án", "confidence": 0.0-1.0}},
    "PhongBan": {{"matched": true/false, "department_id": ID, "department_code": "Mã phòng ban", "department_name": "Tên phòng ban", "confidence": 0.0-1.0}},
    "CongViec": {{"matched": true/false, "task_id": ID, "task_name": "Tên công việc", "confidence": 0.0-1.0}},
    "VanDe": {{"matched": true/false, "issue_id": ID, "issue_description": "Mô tả vấn đề", "confidence": 0.0-1.0}},
    "TienTrinhXuLy": {{"matched": true/false, "progress_id": ID, "progress_status": "Trạng thái", "confidence": 0.0-1.0}}
  }},
  "document_info": {{
    "date": "Ngày ban hành (YYYY-MM-DD)",
    "document_number": "Số hiệu văn bản",
    "issuing_authority": "Cơ quan ban hành",
    "document_type": "Loại tài liệu (BC, QD, CV, etc.)",
    "document_type_name": "Tên đầy đủ của loại tài liệu"
  }},
  "keywords": ["từ khóa 1", "từ khóa 2", "từ khóa 3"],
  "suggested_filename": "Tên file đề xuất theo quy chuẩn",
  "suggested_destination": "Đường dẫn thư mục đề xuất"
}}
"""
    
    def _build_user_prompt(self, text_content: str, data: Dict[str, Any]) -> str:
        """Xây dựng user prompt để gửi đến AI"""
        data_type = data.get("type", "")
        
        prompt = f"""
Hãy phân tích văn bản sau và trích xuất thông tin:

{text_content[:4000]}  # Giới hạn 4000 ký tự để tránh quá dài

"""
        
        if data_type == "file":
            file_info = data.get("metadata", {})
            prompt += f"""
Thông tin file:
- Tên file: {file_info.get('name', 'N/A')}
- Loại file: {file_info.get('type', 'N/A')}
- Kích thước: {file_info.get('size', 'N/A')} bytes
- Ngày sửa đổi: {file_info.get('modified', 'N/A')}

"""
        
        prompt += """
Hãy thực hiện các nhiệm vụ sau:
1. Tóm tắt nội dung chính trong 2-3 câu
2. Xác định loại tài liệu (Quyết định, Báo cáo, Công văn, etc.)
3. Trích xuất thông tin tài liệu (ngày ban hành, số hiệu, cơ quan ban hành)
4. Mapping với các thực thể trong CSDL (Dự án, Phòng ban, Công việc, Vấn đề)
5. Gợi ý tên file theo quy chuẩn YYYYMMDD_MaDuAn_MaPhongBan_Loai_MoTaNgan.ext
6. Gợi ý vị trí lưu file (ví dụ: D:/PMIS_Documents/[MaDuAn]/[LoaiTaiLieu]/)

QUAN TRỌNG: Trả về kết quả dưới dạng JSON VÀ KHÔNG BAO GIỜ bao quanh JSON trong các block code markdown. Chỉ trả về JSON thuần túy.
"""
        
        return prompt
    
    def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi API Gemini để phân tích văn bản"""
        import google.generativeai as genai
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Create the model
        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
        )
        
        # Combine system prompt and user prompt for Gemini
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            response = model.generate_content(combined_prompt)
            
            # Extract the text from the response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return response.parts[0].text
            else:
                logger.error("Unexpected response format from Gemini API")
                raise ValueError("Unexpected response format from Gemini API")
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    def _format_analysis_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Định dạng kết quả phân tích từ Gemini"""
        # Đảm bảo kết quả có đủ các trường cần thiết
        formatted_result = {
            "summary": raw_result.get("summary", ""),
            "mapping_results": {
                "DuAn": raw_result.get("mapping_results", {}).get("DuAn", {"matched": False, "confidence": 0.0}),
                "PhongBan": raw_result.get("mapping_results", {}).get("PhongBan", {"matched": False, "confidence": 0.0}),
                "CongViec": raw_result.get("mapping_results", {}).get("CongViec", {"matched": False, "confidence": 0.0}),
                "VanDe": raw_result.get("mapping_results", {}).get("VanDe", {"matched": False, "confidence": 0.0}),
                "TienTrinhXuLy": raw_result.get("mapping_results", {}).get("TienTrinhXuLy", {"matched": False, "confidence": 0.0})
            },
            "document_info": {
                "date": raw_result.get("document_info", {}).get("date", ""),
                "document_number": raw_result.get("document_info", {}).get("document_number", ""),
                "issuing_authority": raw_result.get("document_info", {}).get("issuing_authority", ""),
                "document_type": raw_result.get("document_info", {}).get("document_type", ""),
                "document_type_name": raw_result.get("document_info", {}).get("document_type_name", "")
            },
            "keywords": raw_result.get("keywords", []),
            "suggested_filename": raw_result.get("suggested_filename", ""),
            "suggested_destination": raw_result.get("suggested_destination", "")
        }
        
        return formatted_result
    
    def _get_default_result(self, error_message: str = "Không thể phân tích nội dung") -> Dict[str, Any]:
        """Trả về kết quả mặc định khi AI không thể phân tích"""
        return {
            "summary": error_message,
            "mapping_results": {
                "DuAn": {"matched": False, "confidence": 0.0},
                "PhongBan": {"matched": False, "confidence": 0.0},
                "CongViec": {"matched": False, "confidence": 0.0},
                "VanDe": {"matched": False, "confidence": 0.0},
                "TienTrinhXuLy": {"matched": False, "confidence": 0.0}
            },
            "document_info": {
                "date": "",
                "document_number": "",
                "issuing_authority": "",
                "document_type": "",
                "document_type_name": ""
            },
            "keywords": [],
            "suggested_filename": "",
            "suggested_destination": ""
        }
    
    def suggest_filename(self, analysis_result: Dict[str, Any], original_filename: str = "") -> str:
        """Đề xuất tên file dựa trên kết quả phân tích"""
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
        """Đề xuất vị trí lưu file"""
        # Nếu AI đã đề xuất vị trí, sử dụng nó
        suggested = analysis_result.get("suggested_destination", "")
        if suggested:
            return suggested
        
        # Nếu không, tự tạo đường dẫn dựa trên kết quả mapping
        base_path = config.DEFAULT_DOCUMENT_PATH
        
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
        
        return base_path