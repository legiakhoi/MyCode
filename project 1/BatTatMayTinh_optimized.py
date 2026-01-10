import telebot
import os
import time
import threading
import subprocess
import logging
import socket
from dotenv import load_dotenv

# --- CẤU HÌNH LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# --- CẤU HÌNH ---
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

# Kiểm tra biến môi trường
if not API_TOKEN or not MY_CHAT_ID:
    logging.error("Chưa cấu hình API_TOKEN hoặc MY_CHAT_ID trong file .env")
    exit(1)

bot = telebot.TeleBot(API_TOKEN)

def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Kiểm tra kết nối internet thực tế thay vì chỉ sleep"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def send_startup_notification():
    """Gửi thông báo khi có mạng"""
    max_retries = 10
    for i in range(max_retries):
        if check_internet():
            try:
                bot.send_message(MY_CHAT_ID, "🟢 THÔNG BÁO: Máy tính đã KHỞI ĐỘNG và có mạng!")
                logging.info("Đã gửi thông báo khởi động.")
                return
            except Exception as e:
                logging.error(f"Lỗi gửi tin nhắn khởi động: {e}")
                return
        
        logging.info(f"Đang đợi mạng... (Lần thử {i+1}/{max_retries})")
        time.sleep(5)
    
    logging.warning("Không thể kết nối mạng sau nhiều lần thử.")

def verify_user(message):
    """Hàm phụ trợ để xác thực người dùng"""
    return str(message.chat.id) == str(MY_CHAT_ID)

@bot.message_handler(commands=['tatmay'])
def handle_shutdown(message):
    if verify_user(message):
        bot.reply_to(message, "🔴 XÁC NHẬN: Đang chuẩn bị tắt máy trong 2 phút...")
        try:
            bot.send_message(MY_CHAT_ID, "⚠️ Máy tính đang thực hiện quy trình tắt nguồn...")
            # Sử dụng subprocess an toàn hơn os.system
            subprocess.run(["shutdown", "/s", "/t", "120"], check=True, shell=True)
            logging.info("Đã thực hiện lệnh tắt máy.")
        except Exception as e:
            logging.error(f"Lỗi khi tắt máy: {e}")
            bot.reply_to(message, f"❌ Lỗi thực thi lệnh: {e}")
    else:
        bot.reply_to(message, "⛔ Bạn không có quyền tắt máy tính này!")
        logging.warning(f"Truy cập trái phép từ ID: {message.chat.id}")

@bot.message_handler(commands=['huytat'])
def handle_cancel_shutdown(message):
    if verify_user(message):
        try:
            subprocess.run(["shutdown", "/a"], check=True, shell=True)
            bot.reply_to(message, "✅ Đã hủy lệnh tắt máy.")
            logging.info("Đã hủy lệnh tắt máy.")
        except Exception as e:
            # Mã lỗi 1116 nghĩa là không có lệnh tắt máy nào đang chạy
            bot.reply_to(message, "ℹ️ Không có lệnh tắt máy nào đang chờ.")
    else:
        bot.reply_to(message, "⛔ Không có quyền!")

if __name__ == "__main__":
    # daemon=True để luồng này tự tắt khi chương trình chính tắt
    threading.Thread(target=send_startup_notification, daemon=True).start()
    
    logging.info("Bot đang chạy...")
    try:
        # Tự động kết nối lại khi mất mạng
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        logging.error(f"Lỗi bot dừng hoạt động: {e}")
