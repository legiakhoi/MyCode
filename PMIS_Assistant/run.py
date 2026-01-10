#!/usr/bin/env python3
"""
Script chạy PMIS Assistant
Sử dụng script này để khởi động ứng dụng
"""

import sys
import os
import subprocess

def main():
    """Hàm chính để chạy ứng dụng"""
    try:
        # Kiểm tra Python version
        if sys.version_info < (3, 8):
            print("Lỗi: PMIS Assistant yêu cầu Python 3.8 hoặc cao hơn")
            return 1
        
        # Thêm thư mục hiện tại vào Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Kiểm tra file .env
        env_file = os.path.join(current_dir, ".env")
        if not os.path.exists(env_file):
            print("Cảnh báo: File .env không tồn tại")
            print("Vui lòng sao chép file .env.example thành .env và cấu hình các thông số cần thiết")
            
            # Hỏi người dùng có muốn tạo file .env không
            response = input("Bạn có muốn tạo file .env mẫu không? (y/n): ")
            if response.lower() in ['y', 'yes']:
                example_file = os.path.join(current_dir, ".env.example")
                if os.path.exists(example_file):
                    import shutil
                    shutil.copy(example_file, env_file)
                    print(f"Đã tạo file .env tại {env_file}")
                    print("Vui lòng chỉnh sửa file .env và chạy lại ứng dụng")
                    return 1
                else:
                    print("Không tìm thấy file .env.example")
                    return 1
            else:
                print("Vui lòng tạo file .env và chạy lại ứng dụng")
                return 1
        
        # Kiểm tra các thư viện cần thiết
        try:
            import PyQt6
            import psycopg
            import requests
            import pynput
            import PIL
            import dotenv
        except ImportError as e:
            print(f"Lỗi: Thiếu thư viện cần thiết: {e}")
            print("Vui lòng chạy: pip install -r requirements.txt")
            return 1
        
        # Chạy ứng dụng chính
        from main import main as app_main
        return app_main()
        
    except KeyboardInterrupt:
        print("\nỨng dụng đã được dừng bởi người dùng")
        return 0
    except Exception as e:
        print(f"Lỗi khi chạy ứng dụng: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())