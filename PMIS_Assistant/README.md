# PMIS Assistant

Ứng dụng Desktop chạy ngầm trên Windows giúp tự động hóa quy trình lưu trữ và phân loại tài liệu/dữ liệu từ Clipboard vào hệ thống cơ sở dữ liệu dự án (PMIS).

## Tính năng chính

- **Lắng nghe Hotkey toàn cục**: Nhấn `Alt+C` để kích hoạt
- **Phân tích AI thông minh**: Sử dụng Z.AI API để phân loại và tóm tắt tài liệu
- **Tích hợp PostgreSQL**: Lưu trữ dữ liệu vào hệ thống PMIS
- **Quản lý file tự động**: Đặt tên file theo quy chuẩn và tổ chức thư mục thông minh
- **Giao diện thân thiện**: UI PyQt6 hiện đại với tree view và filter linh hoạt

## Yêu cầu hệ thống

- **Hệ điều hành**: Windows 10/11
- **Python**: 3.8 hoặc cao hơn
- **Cơ sở dữ liệu**: PostgreSQL 12+
- **RAM**: Tối thiểu 4GB
- **Ổ cứng**: 1GB trống
- **Internet**: Kết nối ổn định để sử dụng Z.AI API

## Cài đặt

### 1. Clone hoặc tải dự án

```bash
git clone <repository-url>
cd PMIS_Assistant
```

### 2. Chạy script cài đặt

```bash
python setup.py
```

Script cài đặt sẽ:
- Kiểm tra phiên bản Python
- Cài đặt các thư viện cần thiết
- Tạo file `.env` từ `.env.example`
- Thiết lập cơ sở dữ liệu
- Tạo shortcut trên Desktop

### 3. Cấu hình môi trường

Chỉnh sửa file `.env` với các thông tin sau:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pmis_db
DB_USER=postgres
DB_PASSWORD=your_password

# Z.AI API Configuration
ZAI_API_KEY=your_zai_api_key_here
ZAI_API_URL=https://api.z.ai/v1/chat/completions

# Application Configuration
DEFAULT_DOCUMENT_PATH=./PMIS_Documents
```

## Cấu trúc dự án

```
PMIS_Assistant/
├── main.py                 # Entry point, lắng nghe hotkey
├── config.py              # Cấu hình ứng dụng
├── .env                   # File chứa API keys và password
├── requirements.txt        # Dependencies
├── database_setup.py      # Script khởi tạo DB
├── run.py                 # Script chạy ứng dụng
├── setup.py               # Script cài đặt
├── src/                   # Source code
│   ├── db_manager.py      # Quản lý kết nối PostgreSQL
│   ├── clipboard_handler.py # Xử lý Clipboard
│   ├── ai_service.py      # Tích hợp Z.AI API
│   ├── ui_app.py          # Giao diện người dùng PyQt6
│   └── file_manager.py    # Quản lý file và thư mục
├── resources/             # Tài nguyên ứng dụng
│   └── icons/            # Icon ứng dụng
└── tests/                # Unit tests
```

## Sử dụng

### 1. Khởi động ứng dụng

- **Từ command line**: `python run.py`
- **Từ Desktop**: Double-click vào shortcut "PMIS Assistant"

Ứng dụng sẽ chạy ngầm và hiển thị icon trong system tray.

### 2. Sử dụng hotkey

1. Sao chép nội dung vào Clipboard (text, ảnh, hoặc file)
2. Nhấn tổ hợp phím `Alt+C`
3. Ứng dụng sẽ tự động:
   - Phân tích nội dung bằng AI
   - Hiển thị UI xác nhận
   - Đề xuất tên file và vị trí lưu
   - Mapping với các bảng trong CSDL

### 3. Xác nhận và lưu

Trong UI xác nhận:

1. **Kiểm tra kết quả AI**: Xem tóm tắt và mapping
2. **Chỉnh sửa (nếu cần)**: Sửa lại nội dung tóm tắt
3. **Chọn bảng và cột**: Chọn các trường cần hiển thị từ CSDL
4. **Filter dữ liệu**: Sử dụng các ô filter để tìm kiếm
5. **Xác nhận vị trí**: Chọn thư mục lưu file
6. **Lưu**: Nhấn "Xác nhận và Lưu"

## Quy trình đặt tên file

File được đặt tên theo quy chuẩn: `YYYYMMDD_MaDuAn_MaPhongBan_Loai_MoTaNgan.ext`

Ví dụ: `20250101_DA001_KT_QD_QuyetDinhMoi.pdf`

Trong đó:
- **YYYYMMDD**: Ngày hiện tại
- **MaDuAn**: Mã dự án từ CSDL
- **MaPhongBan**: Mã phòng ban từ CSDL
- **Loai**: Loại tài liệu (BC, QD, CV, TB, TTr, etc.)
- **MoTaNgan**: Tên file ngắn gọn về nội dung
- **ext**: Phần mở rộng file

## Cấu trúc cơ sở dữ liệu

Ứng dụng sử dụng các bảng chính:

- **DuAn**: Thông tin dự án
- **CongViec**: Công việc thuộc dự án
- **VanDe**: Vấn đề của dự án
- **TienTrinhXuLy**: Tiến trình xử lý
- **PhongBan**: Phòng ban
- **tbl_documents**: Bảng trung tâm lưu trữ file
- **zai_automation_log**: Log hoạt động AI

## Xử lý lỗi

### Lỗi kết nối database
- Kiểm tra PostgreSQL đang chạy
- Xác nhận thông tin trong file `.env`
- Kiểm tra防火墙 settings

### Lỗi Z.AI API
- Xác nhận API key trong file `.env`
- Kiểm tra kết nối internet
- Xác nhận quota API

### Lỗi clipboard
- Đảm bảo có nội dung trong clipboard
- Thử lại với loại nội dung khác
- Kiểm tra quyền truy cập clipboard

## Gỡ cài đặt

1. Dừng ứng dụng (right-click tray icon → Thoát)
2. Xóa shortcut trên Desktop (nếu có)
3. Xóa thư mục dự án
4. Xóa cơ sở dữ liệu (nếu cần)

## Hỗ trợ

### Log file
- Vị trí: `pmis_assistant.log` trong thư mục ứng dụng
- Chứa thông tin chi tiết về lỗi và hoạt động

### Common issues

**Q: Hotkey không hoạt động**
- Kiểm tra ứng dụng đang chạy (tray icon)
- Thử khởi động lại ứng dụng
- Kiểm tra các ứng dụng khác có đang dùng hotkey tương tự

**Q: AI không phân tích được**
- Kiểm tra kết nối internet
- Xác nhận API key Z.AI
- Thử với nội dung ngắn hơn

**Q: Không lưu được file**
- Kiểm tra quyền ghi vào thư mục đích
- Xác nhận đường dẫn hợp lệ
- Kiểm tra dung lượng đĩa trống

## Phát triển

### Cài đặt môi trường phát triển

```bash
# Clone repository
git clone <repository-url>
cd PMIS_Assistant

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt dependencies phát triển
pip install -r requirements-dev.txt
```

### Chạy tests

```bash
python -m pytest tests/
```

### Xây dựng package

```bash
python setup.py sdist bdist_wheel
```

## License

© 2025 PMIS Team. All rights reserved.

## Đóng góp

Vui lòng tạo issue hoặc pull request trên repository.

## Lịch sử thay đổi

### v1.0.0 (2025-01-01)
- Phiên bản đầu tiên
- Tích hợp Z.AI API
- Hỗ trợ PostgreSQL
- Giao diện PyQt6
- Hotkey toàn cục