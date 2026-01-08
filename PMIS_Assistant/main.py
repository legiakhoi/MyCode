#!/usr/bin/env python3
"""
PMIS Assistant - Ứng dụng Desktop hỗ trợ quản lý tài liệu dự án
Entry point chính của ứng dụng
"""

import sys
import os
import logging
import threading
import time
from typing import Optional
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from pynput import keyboard

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from src.clipboard_handler import ClipboardHandler
from src.ai_service import AIService
from src.db_manager import DatabaseManager
from src.file_manager import FileManager
from src.ui_app import show_ui

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pmis_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HotkeyListener(QObject):
    """Lắng nghe hotkey toàn cục"""
    
    # Signal khi hotkey được nhấn
    hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False
        
    def start_listening(self):
        """Bắt đầu lắng nghe hotkey"""
        if self.running:
            return
        
        try:
            # Phân tích hotkey combination
            hotkey_combination = config.HOTKEY_COMBINATION
            
            # Chuyển đổi "alt+c" thành định dạng pynput
            if '+' in hotkey_combination:
                parts = hotkey_combination.lower().split('+')
                key = parts[-1]
                modifiers = parts[:-1]
                
                # Xây dựng hotkey string cho pynput
                hotkey_parts = []
                for mod in modifiers:
                    if mod == 'alt':
                        hotkey_parts.append('<alt>')
                    elif mod == 'ctrl':
                        hotkey_parts.append('<ctrl>')
                    elif mod == 'shift':
                        hotkey_parts.append('<shift>')
                    elif mod == 'cmd' or mod == 'win':
                        hotkey_parts.append('<cmd>')
                
                hotkey_parts.append(key)
                hotkey_string = '+'.join(hotkey_parts)
            else:
                hotkey_string = hotkey_combination
            
            logger.info(f"Starting hotkey listener for: {hotkey_string}")
            
            # Tạo listener
            self.listener = keyboard.GlobalHotKeys({
                hotkey_string: self._on_hotkey
            })
            
            self.listener.start()
            self.running = True
            
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            QMessageBox.critical(None, "Lỗi", f"Không thể khởi tạo hotkey listener: {str(e)}")
    
    def stop_listening(self):
        """Dừng lắng nghe hotkey"""
        if self.listener and self.running:
            self.listener.stop()
            self.running = False
            logger.info("Hotkey listener stopped")
    
    def _on_hotkey(self):
        """Xử lý khi hotkey được nhấn"""
        logger.info("Hotkey pressed")
        self.hotkey_pressed.emit()

class PMISAssistant(QObject):
    """Lớp chính của PMIS Assistant"""
    
    def __init__(self):
        super().__init__()
        
        # Khởi tạo các thành phần
        self.clipboard_handler = ClipboardHandler()
        self.ai_service = AIService()
        self.db_manager = DatabaseManager()
        self.file_manager = FileManager()
        
        # Hotkey listener
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.hotkey_pressed.connect(self.process_clipboard_data)
        
        # System tray
        self.tray_icon = None
        self.setup_system_tray()
        
        # Timer để xử lý các tác vụ nền
        self.timer = QTimer()
        self.timer.timeout.connect(self.cleanup_temp_files)
        self.timer.start(60000)  # Chạy mỗi phút
        
        # Biến để kiểm tra xem UI đang mở không
        self.ui_open = False
    
    def setup_system_tray(self):
        """Thiết lập system tray icon"""
        try:
            # Tạo icon (nếu có file icon)
            icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "pmis_icon.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
            else:
                # Tạo icon mặc định
                icon = self._create_default_icon()
            
            self.tray_icon = QSystemTrayIcon(icon)
            
            # Tạo menu cho tray icon
            tray_menu = QMenu()
            
            # Action về ứng dụng
            about_action = QAction("Về PMIS Assistant", self)
            about_action.triggered.connect(self.show_about)
            tray_menu.addAction(about_action)
            
            tray_menu.addSeparator()
            
            # Action thoát
            exit_action = QAction("Thoát", self)
            exit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(exit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Thiết lập tooltip
            self.tray_icon.setToolTip(f"{config.APP_NAME} v{config.APP_VERSION}")
            
            # Hiển thị tray icon
            self.tray_icon.show()
            
            # Kết nối signal double click
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            logger.info("System tray icon setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup system tray: {e}")
    
    def _create_default_icon(self):
        """Tạo icon mặc định"""
        # Tạo một icon đơn giản
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#4CAF50"))  # Màu xanh lá
        
        # Vẽ chữ "PM" lên icon
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "PM")
        painter.end()
        
        return QIcon(pixmap)
    
    def on_tray_icon_activated(self, reason):
        """Xử lý khi tray icon được kích hoạt"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_about()
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        QMessageBox.information(
            None,
            f"Về {config.APP_NAME}",
            f"{config.APP_NAME} v{config.APP_VERSION}\n\n"
            "Ứng dụng Desktop hỗ trợ quản lý tài liệu dự án\n"
            "Sử dụng AI để phân loại và lưu trữ tài liệu tự động\n\n"
            f"Hotkey: {config.HOTKEY_COMBINATION}\n\n"
            "© 2025 PMIS Team"
        )
    
    def start(self):
        """Khởi động ứng dụng"""
        try:
            # Kiểm tra kết nối database
            if not self.db_manager.test_connection():
                QMessageBox.critical(
                    None, 
                    "Lỗi kết nối", 
                    "Không thể kết nối đến cơ sở dữ liệu. Vui lòng kiểm tra cấu hình."
                )
                return False
            
            # Bắt đầu lắng nghe hotkey
            self.hotkey_listener.start_listening()
            
            logger.info(f"{config.APP_NAME} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            QMessageBox.critical(
                None, 
                "Lỗi khởi động", 
                f"Không thể khởi động ứng dụng: {str(e)}"
            )
            return False
    
    def process_clipboard_data(self):
        """Xử lý dữ liệu từ clipboard"""
        if self.ui_open:
            logger.info("UI already open, ignoring hotkey")
            return
        
        try:
            logger.info("Processing clipboard data...")
            
            # Lấy dữ liệu từ clipboard
            clipboard_data = self.clipboard_handler.get_clipboard_data()
            
            if clipboard_data["type"] == "empty":
                self.show_tray_message(
                    "Clipboard trống", 
                    "Không có dữ liệu trong clipboard để xử lý"
                )
                return
            
            if clipboard_data["type"] == "error":
                self.show_tray_message(
                    "Lỗi clipboard", 
                    f"Không thể lấy dữ liệu từ clipboard: {clipboard_data.get('metadata', {}).get('error', '')}"
                )
                return
            
            # Lấy context từ database
            db_context = self.db_manager.get_main_tables_info()
            
            # Phân tích bằng AI
            logger.info("Analyzing data with AI...")
            ai_result = self.ai_service.analyze_clipboard_data(clipboard_data, db_context)
            
            # Hiển thị UI
            self.ui_open = True
            result = show_ui(clipboard_data, ai_result, self.db_manager, self.file_manager)
            self.ui_open = False
            
            if result == 0:  # QDialog.Accepted
                self.show_tray_message(
                    "Thành công", 
                    "Dữ liệu đã được lưu thành công!"
                )
            
        except Exception as e:
            logger.error(f"Error processing clipboard data: {e}")
            self.show_tray_message(
                "Lỗi xử lý", 
                f"Lỗi khi xử lý dữ liệu: {str(e)}"
            )
    
    def show_tray_message(self, title: str, message: str, duration: int = 3000):
        """Hiển thị thông báo qua system tray"""
        if self.tray_icon and self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)
    
    def cleanup_temp_files(self):
        """Dọn dẹp các file tạm thời"""
        try:
            self.clipboard_handler.cleanup_temp_files()
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def quit_application(self):
        """Thoát ứng dụng"""
        try:
            logger.info("Shutting down application...")
            
            # Dừng hotkey listener
            self.hotkey_listener.stop_listening()
            
            # Đóng kết nối database
            self.db_manager.close()
            
            # Thoát QApplication
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            QApplication.quit()

def main():
    """Hàm chính"""
    try:
        # Kiểm tra cấu hình
        try:
            config.validate_config()
        except ValueError as e:
            QMessageBox.critical(
                None, 
                "Lỗi cấu hình", 
                f"Cấu hình không hợp lệ: {str(e)}\n\n"
                "Vui lòng kiểm tra file .env và đảm bảo các biến cần thiết đã được thiết lập."
            )
            return 1
        
        # Tạo QApplication
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # Không thoát khi cửa sổ đóng
        
        # Khởi tạo PMIS Assistant
        pmis_assistant = PMISAssistant()
        
        # Khởi động ứng dụng
        if not pmis_assistant.start():
            return 1
        
        # Chạy event loop
        return app.exec()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        QMessageBox.critical(
            None, 
            "Lỗi nghiêm trọng", 
            f"Ứng dụng gặp lỗi nghiêm trọng: {str(e)}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())