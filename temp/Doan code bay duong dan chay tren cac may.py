import platform
import os

# --- PHẦN CẤU HÌNH TỰ ĐỘNG ---

# 1. Lấy tên máy tính đang chạy
ten_may_tinh = platform.node()
print(f"--> Đang chạy trên máy: {ten_may_tinh}")

# 2. Bộ lọc thông minh để chọn đường dẫn
# Bạn thay 'TÊN_MÁY_...' bằng tên thật lấy từ lệnh hostname
# Thay đường dẫn r"..." bằng đường dẫn folder dữ liệu thật trên máy đó

# Thay thế "TÊN_MÁY_ẢO_CỦA_BẠN" bằng tên máy thật của bạn (chạy lệnh 'hostname' trong terminal để xem)
if "TÊN_MÁY_ẢO_CỦA_BẠN" in ten_may_tinh: 
    # Cấu hình cho MÁY ẢO (Nơi chạy Task Scheduler)
    # Ví dụ: Tên máy là 'pc-on-nas'
    # Đường dẫn nên là ổ mạng map sẵn hoặc đường dẫn mạng
    base_path = r"Z:\\" 
    print("phát hiện môi trường MÁY ẢO NAS.")

# Thay thế "TÊN_MÁY_BÀN_CỦA_BẠN" bằng tên máy thật của bạn
elif "TÊN_MÁY_BÀN_CỦA_BẠN" in ten_may_tinh:
    # Cấu hình cho MÁY BÀN
    # Ví dụ: Tên máy là 'Desktop-KhoiLG'
    base_path = r"D:\\SynologyDrive\\DuLieu_DuAn"
    print("Phát hiện môi trường MÁY BÀN.")

# Thay thế "TÊN_LAPTOP_CỦA_BẠN" bằng tên máy thật của bạn
elif "TÊN_LAPTOP_CỦA_BẠN" in ten_may_tinh:
    # Cấu hình cho LAPTOP
    # Ví dụ: Tên máy là 'Laptop-Dell-XPS'
    base_path = r"C:\\Users\\KhoiLG\\SynologyDrive\\DuLieu_DuAn"
    print("Phát hiện môi trường LAPTOP.")

else:
    # Trường hợp dự phòng (Nếu mang sang máy lạ)
    print("CẢNH BÁO: Máy lạ, không nhận diện được đường dẫn!")
    base_path = os.getcwd()  # Sử dụng thư mục hiện tại làm mặc định

# Kiểm tra xem đường dẫn có tồn tại không
if not os.path.exists(base_path):
    print(f"CẢNH BÁO: Đường dẫn {base_path} không tồn tại! Sử dụng thư mục hiện tại.")
    base_path = os.getcwd()

# --- KẾT THÚC CẤU HÌNH ---

# --- BẮT ĐẦU CODE XỬ LÝ CỦA BẠN TỪ ĐÂY ---

# Từ giờ trở đi, khi cần gọi file, bạn hãy dùng biến 'base_path'
# Ví dụ: Bạn muốn mở file 'Bao_cao.xlsx' nằm trong thư mục dữ liệu

# Cách viết cũ (Gây lỗi): 
# file_can_mo = r"D:\SynologyDrive\DuLieu_DuAn\Bao_cao.xlsx"

# Cách viết mới (Thông minh):
try:
    file_can_mo = os.path.join(base_path, "Bao_cao.xlsx")
    if not os.path.isfile(file_can_mo):
        raise FileNotFoundError(f"File {file_can_mo} không tồn tại!")
    print(f"Đang xử lý file tại: {file_can_mo}")
    # [Code xử lý dữ liệu của bạn ở dưới này...]
except FileNotFoundError as e:
    print(f"Lỗi: {e}")
except Exception as e:
    print(f"Lỗi không mong đợi: {e}")