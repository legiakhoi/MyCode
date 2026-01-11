# 1. Giữ nguyên
FROM python:3.9-slim

# 2. Bỏ dòng WORKDIR /app nếu không thực sự cần thiết tùy chỉnh
# VS Code tự động mount vào /workspaces/tên-project-của-bạn
# Nếu muốn giữ lại để dễ quản lý thì cũng được:
WORKDIR /app

# 3. QUAN TRỌNG: Chỉ copy file requirements trước để tận dụng cache
# (Chỉ chạy lệnh này nếu file requirements.txt thực sự tồn tại)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Cập nhật hệ điều hành cơ bản (Tùy chọn, giúp tránh lỗi thiếu thư viện git, curl...)
RUN apt-get update && apt-get install -y git curl

# 5. Giữ nguyên lệnh này để container không bị tắt
CMD ["tail", "-f", "/dev/null"]