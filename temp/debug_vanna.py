import sys
import os

print("--- BẮT ĐẦU KIỂM TRA ---")

# 1. Kiểm tra xem Python tìm thấy vanna ở đâu
try:
    import vanna
    print(f"1. Đường dẫn thư mục vanna: {os.path.dirname(vanna.__file__)}")
    
    # 2. Liệt kê tất cả các file trong thư mục vanna
    folder_path = os.path.dirname(vanna.__file__)
    files = os.listdir(folder_path)
    print(f"2. Các file có trong thư mục này: {files}")
    
    # 3. Kiểm tra xem có file remote.py không
    if 'remote.py' in files:
        print(">>> KẾT QUẢ: File remote.py CÓ tồn tại. Đang thử import...")
        from vanna.remote import VannaDefault
        print(">>> THÀNH CÔNG: Đã import được VannaDefault! Bạn có thể quay lại chạy file Chat2DB.py")
    else:
        print(">>> LỖI NGHIÊM TRỌNG: Không thấy file remote.py đâu cả. Gói cài đặt bị hỏng.")
        
except ImportError as e:
    print(f"Lỗi Import: {e}")
except Exception as e:
    print(f"Lỗi khác: {e}")