import pandas as pd
import os

print("--- CHÀO MỪNG ĐẾN VỚI DOCKER ---")

# Tạo một bộ dữ liệu giả lập
data = {
    'Ten': ['Du An A', 'Du An B', 'Du An C'],
    'TrangThai': ['Hoan thanh', 'Dang lam', 'Chua lam'],
    'Diem': [10, 8, 0]
}

# Chuyển thành bảng (DataFrame)
df = pd.DataFrame(data)

print("\nĐây là bảng dữ liệu chạy trong môi trường Container:")
print(df)

print("\nĐang chạy trên hệ điều hành (bên trong container):")
print(os.name) # Nếu ra 'posix' là Linux, dù máy thật của bạn là Windows