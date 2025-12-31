import telebot
import os
import time
import threading
from dotenv import load_dotenv

# --- CẤU HÌNH --- máy 2
load_dotenv()  # Load biến môi trường từ file .env
API_TOKEN = os.getenv('API_TOKEN')  # Dán Token vào đây
MY_CHAT_ID = os.getenv('MY_CHAT_ID')   # Dán ID số của bạn vào đây (Dạng string hoặc số đều được)

bot = telebot.TeleBot(API_TOKEN)

def send_startup_notification():
    """Gửi thông báo khi script bắt đầu chạy (tức là khi máy bật)"""
    try:
        # Đợi một chút để mạng kết nối ổn định sau khi khởi động
        time.sleep(10) 
        bot.send_message(MY_CHAT_ID, "🟢 THÔNG BÁO: Máy tính của bạn đã KHỞI ĐỘNG và đang trực tuyến!")
    except Exception as e:
        print(f"Lỗi gửi tin nhắn khởi động: {e}")

# Xử lý lệnh tắt máy
@bot.message_handler(commands=['tatmay'])
def handle_shutdown(message):
    # Bảo mật: Chỉ thực hiện nếu người gửi là chính bạn
    if str(message.chat.id) == str(MY_CHAT_ID):
        bot.reply_to(message, "🔴 XÁC NHẬN: Đang chuẩn bị tắt máy trong 2 phút...")
        
        # Gửi thông báo chuẩn bị tắt máy (theo yêu cầu của bạn)
        bot.send_message(MY_CHAT_ID, "⚠️ Máy tính đang thực hiện quy trình tắt nguồn...")
        
        # Thực hiện lệnh tắt máy của Windows (hẹn giờ 10s để kịp gửi tin nhắn)
        os.system("shutdown /s /t 120") 
    else:
        bot.reply_to(message, "⛔ Bạn không có quyền tắt máy tính này!")

# Xử lý lệnh hủy tắt máy (phòng khi bấm nhầm)
@bot.message_handler(commands=['huytat'])
def handle_cancel_shutdown(message):
    if str(message.chat.id) == str(MY_CHAT_ID):
        os.system("shutdown /a")
        bot.reply_to(message, "✅ Đã hủy lệnh tắt máy.")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # Chạy luồng gửi thông báo khởi động riêng để không chặn việc nhận tin nhắn
    threading.Thread(target=send_startup_notification).start()
    
    # Bắt đầu lắng nghe tin nhắn liên tục
    print("Bot đang chạy...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Lỗi kết nối: {e}")