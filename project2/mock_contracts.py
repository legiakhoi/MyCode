import pandas as pd
import numpy as np

print("--- TÌM HỢP ĐỒNG CÓ GIÁ TRỊ CAO NHẤT (MÔ PHỎNG) ---")

# 1. Tạo dữ liệu giả lập dựa trên cấu trúc bảng HopDong
# Cấu trúc: ID, SoHopDong, GiaTriHopDong, NgayKy, is_deleted
data = {
    'ID': [1, 2, 3, 4, 5, 6],
    'SoHopDong': ['HD-2023-001', 'HD-2023-002', 'HD-2023-003', 'HD-2023-004', 'HD-2023-005', 'HD-DELETED'],
    'GiaTriHopDong': [
        1500000000.00,  # 1.5 tỷ
        5000000000.00,  # 5 tỷ (Cao nhất)
        2000000000.00,  # 2 tỷ
        5000000000.00,  # 5 tỷ (Cao nhất - đồng hạng)
        1200000000.00,  # 1.2 tỷ
        9000000000.00   # 9 tỷ (Nhưng đã bị xóa)
    ],
    'NgayKy': [
        '2023-01-15', 
        '2023-03-20', 
        '2023-06-10', 
        '2023-08-05', 
        '2023-11-12',
        '2023-01-01'
    ],
    'is_deleted': [False, False, False, False, False, True]
}

df = pd.DataFrame(data)

print("\nDữ liệu hợp đồng mô phỏng:")
print(df[['ID', 'SoHopDong', 'GiaTriHopDong', 'is_deleted']])

# 2. Lọc bỏ các bản ghi đã xóa (is_deleted = True)
active_contracts = df[df['is_deleted'] == False]

# 3. Tìm giá trị cao nhất
if not active_contracts.empty:
    max_value = active_contracts['GiaTriHopDong'].max()
    
    # 4. Lấy danh sách các hợp đồng có giá trị bằng giá trị cao nhất
    result = active_contracts[active_contracts['GiaTriHopDong'] == max_value]
    
    print(f"\nGiá trị hợp đồng cao nhất tìm được: {max_value:,.2f}")
    print("\nDanh sách các hợp đồng đạt giá trị cao nhất:")
    print(result[['ID', 'SoHopDong', 'GiaTriHopDong', 'NgayKy']])
else:
    print("\nKhông tìm thấy hợp đồng nào hợp lệ.")
