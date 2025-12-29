import sys
import os

print("1. Đang kiểm tra đường dẫn Python...")
print(sys.executable)

print("\n2. Đang kiểm tra vị trí thư viện Vanna...")
try:
    import vanna
    print(f"Vanna được lấy từ: {vanna.__file__}")
    
    # Kiểm tra xem folder cài đặt có đúng là trong pmis_env không
    if "pmis_env" in vanna.__file__:
        print(">>> OK: Thư viện đang chạy từ môi trường ảo chính xác.")
    else:
        print(">>> CẢNH BÁO: Python đang lấy Vanna sai chỗ (có thể do trùng tên file/folder).")
        
    print("\n3. Thử import module Remote...")
    from vanna.remote import VannaDefault
    print(">>> THÀNH CÔNG: Đã import được VannaDefault!")
    
except ImportError as e:
    print(f"\n>>> VẪN LỖI: {e}")
    print("Lời khuyên: Hãy chắc chắn trong thư mục code KHÔNG CÓ file/folder tên là 'vanna'.")
except Exception as e:
    print(f"\n>>> LỖI KHÁC: {e}")