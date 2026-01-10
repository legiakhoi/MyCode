# Multi-Machine Runner - Hướng dẫn sử dụng

## Tổng quan

Script `multi_machine_runner.py` giúp chạy code Python trên nhiều máy tính khác nhau với cấu hình đường dẫn tự động. Script sẽ tự động phát hiện tên máy và chọn đường dẫn dữ liệu phù hợp.

## Cấu trúc file

```
.
├── machine_config.json      # File cấu hình cho từng máy
├── multi_machine_runner.py  # Script chính
└── README_MULTI_MACHINE.md  # File hướng dẫn này
```

## Cách sử dụng

### Bước 1: Tìm tên máy tính của bạn

Mở terminal/cmd và chạy lệnh:

```bash
hostname
```

Hoặc chạy Python:

```python
import platform
print(platform.node())
```

### Bước 2: Cấu hình file `machine_config.json`

Mở file [`machine_config.json`](machine_config.json) và cập nhật thông tin:

```json
{
  "machines": {
    "MÁY_ẢO_NAS": {
      "name_pattern": ["pc-on-nas", "tên-máy-của-bạn"],
      "base_path": "Z:\\",
      "environment": "VIRTUAL_MACHINE"
    },
    "MÁY_BÀN": {
      "name_pattern": ["Desktop-KhoiLG", "tên-máy-của-bạn"],
      "base_path": "D:\\SynologyDrive\\DuLieu_DuAn",
      "environment": "DESKTOP"
    }
  }
}
```

**Lưu ý:**
- Thay thế `"tên-máy-của-bạn"` bằng tên máy thật (lấy từ Bước 1)
- Có thể thêm nhiều tên máy vào mảng `name_pattern`
- `base_path` là đường dẫn đến thư mục dữ liệu của bạn

### Bước 3: Chạy script

```bash
python multi_machine_runner.py
```

## API - Các phương thức hữu ích

```python
from multi_machine_runner import MachineConfig

# Khởi tạo
config = MachineConfig()

# Lấy đường dẫn đầy đủ đến file
file_path = config.get_path("Bao_cao.xlsx")

# Kiểm tra file có tồn tại không
if config.file_exists("Bao_cao.xlsx"):
    print("File tồn tại!")

# Liệt kê file theo pattern
files = config.list_files("*.xlsx")

# Lấy thông tin cấu hình
info = config.get_info()
print(info['machine_name'])  # Tên máy
print(info['base_path'])     # Đường dẫn
print(info['environment'])   # Môi trường
```

## Ví dụ tích hợp với code của bạn

```python
from multi_machine_runner import MachineConfig
import pandas as pd

# Khởi tạo cấu hình
config = MachineConfig()

# Đọc file Excel
try:
    file_path = config.get_path("Bao_cao.xlsx")
    df = pd.read_excel(file_path)
    print(f"Đã đọc {len(df)} dòng dữ liệu")
    
    # Xử lý dữ liệu...
    
except FileNotFoundError:
    print(f"Không tìm thấy file tại: {file_path}")
except Exception as e:
    print(f"Lỗi: {e}")
```

## Các vấn đề đã được sửa so với bản cũ

| Vấn đề | Bản cũ | Bản mới |
|--------|--------|---------|
| Logic so sánh tên máy | Sai (kiểm tra placeholder trong tên máy) | Đúng (kiểm tra tên máy trong pattern) |
| Cấu hình | Hardcode trong script | Tách ra file JSON riêng |
| Đường dẫn | Format không chuẩn | Sử dụng `os.path.join` |
| Xử lý lỗi | Cơ bản | Chi tiết với try-except |
| Mở rộng | Khó | Dễ thêm máy mới |

## Cấu hình chi tiết

### Thêm máy mới vào config

```json
{
  "machines": {
    "MÁY_MỚI": {
      "name_pattern": ["Tên-Máy-Mới", "PC-XYZ"],
      "description": "Mô tả máy",
      "base_path": "C:\\DuLieu",
      "environment": "NEW_MACHINE"
    }
  }
}
```

### Cài đặt tùy chọn

```json
{
  "settings": {
    "auto_create_folder": false,      // Tự động tạo thư mục nếu không tồn tại
    "show_debug_info": true,          // Hiển thị thông tin debug
    "fallback_to_current_dir": true  // Fallback về thư mục hiện tại
  }
}
```

## Khắc phục sự cố

### Lỗi "Không tìm thấy file cấu hình"

- Đảm bảo file [`machine_config.json`](machine_config.json) nằm cùng thư mục với script
- Hoặc truyền đường dẫn đầy đủ: `MachineConfig("path/to/config.json")`

### Lỗi "Đường dẫn không tồn tại"

- Kiểm tra lại `base_path` trong file config
- Bật `fallback_to_current_dir: true` để tự động dùng thư mục hiện tại

### Máy không được nhận diện

- Chạy `hostname` để lấy tên máy chính xác
- Thêm tên máy vào mảng `name_pattern` trong config

## Yêu cầu hệ thống

- Python 3.6+
- Không cần thư viện bên ngoài (chỉ dùng thư viện chuẩn)
