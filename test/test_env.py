import os
from dotenv import load_dotenv # Thêm dòng này

# 1. Nạp key từ file .env lên
load_dotenv()

# 2. Lấy key ra sử dụng (Thay vì điền trực tiếp key vào đây)
# Nếu không tìm thấy key, nó sẽ trả về None
api_key = os.getenv("GROQ_API_KEY") 

# Kiểm tra xem đã lấy được chưa (chỉ dùng để test, xong thì xóa dòng print đi)
if not api_key:
    print("Lỗi: Không tìm thấy API Key trong file .env!")
else:
    print("Đã nạp API Key thành công.")

# ... Các đoạn code phía sau dùng biến api_key bình thường ...
client = Groq(api_key=api_key)