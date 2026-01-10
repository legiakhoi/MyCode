"""
Multi-Machine Runner - Script chạy trên nhiều máy với cấu hình tự động

Tính năng:
- Tự động phát hiện tên máy và chọn đường dẫn phù hợp
- Đọc cấu hình từ file JSON riêng biệt
- Xử lý lỗi và thông báo chi tiết
- Hỗ trợ fallback khi đường dẫn không tồn tại
"""

import platform
import os
import json
from pathlib import Path
from typing import Dict, Optional, Any


class MachineConfig:
    """Lớp quản lý cấu hình cho từng máy"""
    
    def __init__(self, config_file: str = "machine_config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.current_machine: str = platform.node()
        self.base_path: str = ""
        self.environment: str = ""
        
        self._load_config()
        self._detect_machine()
    
    def _load_config(self) -> None:
        """Đọc file cấu hình JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            if self.config.get('settings', {}).get('show_debug_info', True):
                print(f"✓ Đã tải cấu hình từ: {self.config_file}")
        except FileNotFoundError:
            print(f"⚠ CẢNH BÁO: Không tìm thấy file cấu hình '{self.config_file}'")
            print(f"→ Sử dụng cấu hình mặc định (thư mục hiện tại)")
            self.config = {
                "default_config": {
                    "base_path": ".",
                    "environment": "UNKNOWN"
                },
                "settings": {
                    "show_debug_info": True
                }
            }
        except json.JSONDecodeError as e:
            print(f"✗ Lỗi đọc file cấu hình: {e}")
            raise
    
    def _detect_machine(self) -> None:
        """Phát hiện máy đang chạy và gán đường dẫn phù hợp"""
        machine_name = self.current_machine.lower()
        
        if self.config.get('settings', {}).get('show_debug_info', True):
            print(f"→ Tên máy đang chạy: {self.current_machine}")
        
        # Duyệt qua danh sách máy đã cấu hình
        machines = self.config.get('machines', {})
        
        for machine_key, machine_info in machines.items():
            name_patterns = machine_info.get('name_pattern', [])
            
            # Kiểm tra nếu tên máy khớp với bất kỳ pattern nào
            for pattern in name_patterns:
                if pattern.lower() in machine_name:
                    self.base_path = machine_info.get('base_path', '.')
                    self.environment = machine_info.get('environment', 'UNKNOWN')
                    
                    if self.config.get('settings', {}).get('show_debug_info', True):
                        print(f"✓ Phát hiện môi trường: {machine_info.get('description', machine_key)}")
                        print(f"✓ Đường dẫn dữ liệu: {self.base_path}")
                    
                    self._validate_path()
                    return
        
        # Nếu không tìm thấy máy nào, sử dụng cấu hình mặc định
        self._use_default_config()
    
    def _validate_path(self) -> None:
        """Kiểm tra đường dẫn có tồn tại không"""
        if not os.path.exists(self.base_path):
            settings = self.config.get('settings', {})
            
            print(f"⚠ CẢNH BÁO: Đường dẫn '{self.base_path}' không tồn tại!")
            
            if settings.get('fallback_to_current_dir', True):
                self.base_path = os.getcwd()
                print(f"→ Sử dụng thư mục hiện tại: {self.base_path}")
            else:
                raise FileNotFoundError(f"Đường dẫn không tồn tại: {self.base_path}")
    
    def _use_default_config(self) -> None:
        """Sử dụng cấu hình mặc định khi không phát hiện được máy"""
        default_config = self.config.get('default_config', {})
        self.base_path = default_config.get('base_path', '.')
        self.environment = default_config.get('environment', 'UNKNOWN')
        
        print(f"⚠ Không nhận diện được máy '{self.current_machine}'")
        print(f"→ Sử dụng cấu hình mặc định: {self.base_path}")
        
        self._validate_path()
    
    def get_path(self, *path_parts: str) -> str:
        """Lấy đường dẫn đầy đủ đến file/thư mục"""
        return os.path.join(self.base_path, *path_parts)
    
    def file_exists(self, filename: str) -> bool:
        """Kiểm tra file có tồn tại không"""
        return os.path.isfile(self.get_path(filename))
    
    def list_files(self, pattern: str = "*") -> list:
        """Liệt kê file trong thư mục theo pattern"""
        from glob import glob
        return glob(self.get_path(pattern))
    
    def get_info(self) -> Dict[str, str]:
        """Lấy thông tin cấu hình hiện tại"""
        return {
            "machine_name": self.current_machine,
            "base_path": self.base_path,
            "environment": self.environment
        }


def main():
    """Hàm chính - Ví dụ sử dụng"""
    print("=" * 60)
    print(" MULTI-MACHINE RUNNER ".center(60, "="))
    print("=" * 60)
    print()
    
    # Khởi tạo cấu hình
    try:
        config = MachineConfig()
    except Exception as e:
        print(f"✗ Lỗi khởi tạo: {e}")
        return
    
    print()
    print("-" * 60)
    print(" THÔNG TIN CẤU HÌNH ".center(60, "-"))
    print("-" * 60)
    
    info = config.get_info()
    print(f"  Máy tính: {info['machine_name']}")
    print(f"  Môi trường: {info['environment']}")
    print(f"  Đường dẫn: {info['base_path']}")
    print("-" * 60)
    print()
    
    # ============================================
    # BẮT ĐẦU CODE XỬ LÝ CỦA BẠN TỪ ĐÂY
    # ============================================
    
    # Ví dụ 1: Kiểm tra và mở file
    example_filename = "Bao_cao.xlsx"
    
    print(f"→ Đang kiểm tra file: {example_filename}")
    
    if config.file_exists(example_filename):
        file_path = config.get_path(example_filename)
        print(f"✓ Tìm thấy file tại: {file_path}")
        
        # Code xử lý file của bạn ở đây...
        # Ví dụ:
        # import pandas as pd
        # df = pd.read_excel(file_path)
        # print(f"→ Đã đọc file với {len(df)} dòng")
        
    else:
        print(f"✗ File '{example_filename}' không tồn tại trong thư mục dữ liệu")
        print(f"  Thư mục: {config.base_path}")
        
        # Liệt kê các file có sẵn
        available_files = config.list_files("*")
        if available_files:
            print(f"\nCác file có sẵn trong thư mục:")
            for f in available_files[:10]:  # Hiển thị tối đa 10 file
                print(f"  - {os.path.basename(f)}")
    
    print()
    print("-" * 60)
    print(" KẾT THÚC ".center(60, "-"))
    print("-" * 60)


if __name__ == "__main__":
    main()
