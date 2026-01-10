#!/usr/bin/env python3
"""
Script tạo icon đơn giản cho PMIS Assistant
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """Tạo icon cho ứng dụng"""
    # Kích thước icon
    sizes = [16, 32, 48, 64, 128, 256]
    
    # Tạo thư mục icons nếu chưa tồn tại
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    
    for size in sizes:
        # Tạo ảnh mới với nền trong suốt
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Vẽ hình tròn nền
        margin = size // 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(76, 175, 80, 255)  # Màu xanh lá
        )
        
        # Vẽ chữ "PM"
        try:
            # Thử sử dụng font Arial
            font_size = max(size // 4, 8)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Nếu không có font, sử dụng font mặc định
            font = ImageFont.load_default()
        
        text = "PM"
        # Tính kích thước text để căn giữa
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Vị trí text để căn giữa
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # Vẽ text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Lưu ảnh
        img.save(os.path.join(os.path.dirname(__file__), f"pmis_icon_{size}x{size}.png"))
    
    # Lưu phiên bản 32x32 làm icon chính
    img_32 = Image.open(os.path.join(os.path.dirname(__file__), "pmis_icon_32x32.png"))
    img_32.save(os.path.join(os.path.dirname(__file__), "pmis_icon.png"))
    
    print("Đã tạo icon thành công!")

if __name__ == "__main__":
    create_icon()