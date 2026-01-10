#!/usr/bin/env python3
"""
Script cài đặt PMIS Assistant
Sử dụng script này để cài đặt ứng dụng và các phụ thuộc
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Kiểm tra phiên bản Python"""
    if sys.version_info < (3, 8):
        print("Lỗi: PMIS Assistant yêu cầu Python 3.8 hoặc cao hơn")
        print(f"Phiên bản hiện tại: {sys.version}")
        return False
    return True

def install_dependencies():
    """Cài đặt các thư viện cần thiết"""
    print("Đang cài đặt các thư viện cần thiết...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("Đã cài đặt thành công các thư viện cần thiết")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi cài đặt thư viện: {e}")
        return False

def setup_environment():
    """Thiết lập môi trường"""
    print("Đang thiết lập môi trường...")
    
    # Kiểm tra file .env
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("Tạo file .env từ .env.example...")
            shutil.copy(env_example, env_file)
            print("Đã tạo file .env")
            print("Vui lòng chỉnh sửa file .env với các thông tin:")
            print("- DB_PASSWORD: Mật khẩu PostgreSQL")
            print("- GEMINI_API_KEY: API key cho Gemini")
            print("- DEFAULT_DOCUMENT_PATH: Thư mục mặc định để lưu tài liệu")
        else:
            print("Cảnh báo: Không tìm thấy file .env.example")
            print("Vui lòng tạo file .env thủ công")
    else:
        print("File .env đã tồn tại")
    
    # Tạo thư mục mặc định cho tài liệu
    from config import DEFAULT_DOCUMENT_PATH
    doc_path = Path(DEFAULT_DOCUMENT_PATH)
    if not doc_path.exists():
        print(f"Tạo thư mục mặc định: {DEFAULT_DOCUMENT_PATH}")
        try:
            doc_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Không thể tạo thư mục mặc định: {e}")
            print("Sử dụng thư mục Documents của người dùng")
            # Sử dụng thư mục Documents của người dùng
            import os
            user_docs = Path(os.path.expanduser("~/Documents/PMIS_Documents"))
            user_docs.mkdir(parents=True, exist_ok=True)
            print(f"Đã tạo thư mục thay thế: {user_docs}")
    
    return True

def setup_database():
    """Thiết lập cơ sở dữ liệu"""
    print("Đang thiết lập cơ sở dữ liệu...")
    try:
        subprocess.check_call([sys.executable, "database_setup.py"])
        print("Đã thiết lập thành công cơ sở dữ liệu")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thiết lập cơ sở dữ liệu: {e}")
        print("Vui lòng kiểm tra cấu hình PostgreSQL trong file .env")
        return False

def create_desktop_shortcut():
    """Tạo shortcut trên desktop (Windows)"""
    if sys.platform != "win32":
        return True
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "PMIS Assistant.lnk")
        target = os.path.join(os.getcwd(), "run.py")
        wDir = os.getcwd()
        icon = os.path.join(os.getcwd(), "resources", "icons", "pmis_icon.png")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon if os.path.exists(icon) else sys.executable
        shortcut.save()
        
        print("Đã tạo shortcut trên Desktop")
        return True
    except ImportError:
        print("Không thể tạo shortcut (thiếu thư viện winshell)")
        print("Chạy: pip install winshell để tạo shortcut")
        return True
    except Exception as e:
        print(f"Lỗi khi tạo shortcut: {e}")
        return True  # Không phải là lỗi nghiêm trọng

def main():
    """Hàm chính"""
    print("=== PMIS Assistant Setup ===")
    print()
    
    # Kiểm tra phiên bản Python
    if not check_python_version():
        return 1
    
    # Cài đặt thư viện
    if not install_dependencies():
        return 1
    
    # Thiết lập môi trường
    if not setup_environment():
        return 1
    
    # Thiết lập cơ sở dữ liệu
    if not setup_database():
        return 1
    
    # Tạo shortcut
    create_desktop_shortcut()
    
    print()
    print("=== Cài đặt hoàn tất ===")
    print()
    print("Để chạy ứng dụng:")
    print("1. Chạy file run.py")
    print("2. Hoặc sử dụng shortcut trên Desktop (nếu đã được tạo)")
    print()
    print("Hotkey mặc định: Ctrl+C")
    print()
    print("Lưu ý quan trọng:")
    print("- Đảm bảo PostgreSQL đang chạy")
    print("- Kiểm tra lại file .env với các thông tin đúng")
    print("- Cần có kết nối internet để sử dụng Gemini API")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())