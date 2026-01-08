import sys
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTextEdit, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QGroupBox,
    QFileDialog, QMessageBox, QComboBox, QFrame, QScrollArea,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.db_manager import DatabaseManager
from src.file_manager import FileManager

logger = logging.getLogger(__name__)

class TableColumnSelectionDialog(QDialog):
    """Dialog để chọn các cột từ nhiều bảng"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_columns = {}  # {table_name: [column_names]}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Chọn bảng và cột")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Tree widget để hiển thị các bảng và cột
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Bảng/Cột", "Kiểu dữ liệu"])
        self.tree_widget.setColumnWidth(0, 300)
        
        # Thêm các bảng và cột vào tree
        self._populate_tree()
        
        # Cho phép chọn nhiều mục
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        
        layout.addWidget(self.tree_widget)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _populate_tree(self):
        """Điền dữ liệu vào tree widget"""
        try:
            tables = self.db_manager.get_all_tables()
            
            for table_name in tables:
                # Tạo item cho bảng
                table_item = QTreeWidgetItem(self.tree_widget)
                table_item.setText(0, table_name)
                table_item.setText(1, "TABLE")
                table_item.setCheckState(0, Qt.CheckState.Unchecked)
                
                # Lấy các cột của bảng
                columns = self.db_manager.get_table_columns(table_name)
                
                for column in columns:
                    column_item = QTreeWidgetItem(table_item)
                    column_item.setText(0, column['column_name'])
                    column_item.setText(1, column['data_type'])
                    column_item.setCheckState(0, Qt.CheckState.Unchecked)
        
        except Exception as e:
            logger.error(f"Error populating tree: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách bảng: {str(e)}")
    
    def accept_selection(self):
        """Xử lý khi người dùng nhấn OK"""
        self.selected_columns = {}
        
        # Duyệt qua tất cả các item trong tree
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            table_item = root.child(i)
            table_name = table_item.text(0)
            
            # Kiểm tra xem bảng có được chọn không
            if table_item.checkState(0) == Qt.CheckState.Checked:
                # Nếu bảng được chọn, lấy tất cả các cột
                self.selected_columns[table_name] = []
                for j in range(table_item.childCount()):
                    column_item = table_item.child(j)
                    column_name = column_item.text(0)
                    self.selected_columns[table_name].append(column_name)
            else:
                # Nếu bảng không được chọn, kiểm tra các cột con
                selected_columns_for_table = []
                for j in range(table_item.childCount()):
                    column_item = table_item.child(j)
                    if column_item.checkState(0) == Qt.CheckState.Checked:
                        column_name = column_item.text(0)
                        selected_columns_for_table.append(column_name)
                
                if selected_columns_for_table:
                    self.selected_columns[table_name] = selected_columns_for_table
        
        if not self.selected_columns:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một cột")
            return
        
        self.accept()
    
    def get_selected_columns(self) -> Dict[str, List[str]]:
        """Trả về các cột đã chọn"""
        return self.selected_columns

class DestinationFolderDialog(QDialog):
    """Dialog để chọn thư mục đích"""
    
    def __init__(self, file_manager: FileManager, suggested_path: str = "", parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.suggested_path = suggested_path
        self.selected_path = suggested_path
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Chọn vị trí lưu file")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Hiển thị đường dẫn đề xuất
        path_label = QLabel("Đường dẫn đề xuất:")
        layout.addWidget(path_label)
        
        self.path_edit = QLineEdit(self.suggested_path)
        layout.addWidget(self.path_edit)
        
        # Tree widget để hiển thị cấu trúc thư mục
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Thư mục/File"])
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        browse_button = QPushButton("Duyệt...")
        browse_button.clicked.connect(self.browse_folder)
        button_layout.addWidget(browse_button)
        
        button_layout.addStretch()
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Tải cấu trúc thư mục
        self.load_directory_tree()
    
    def load_directory_tree(self):
        """Tải cấu trúc thư mục"""
        try:
            base_path = config.DEFAULT_DOCUMENT_PATH
            tree_data = self.file_manager.get_directory_tree(base_path)
            self._build_tree(tree_data, self.tree_widget.invisibleRootItem())
            self.tree_widget.expandAll()
        except Exception as e:
            logger.error(f"Error loading directory tree: {e}")
    
    def _build_tree(self, node_data: Dict, parent_item: QTreeWidgetItem):
        """Xây dựng cây thư mục từ dữ liệu"""
        if "error" in node_data:
            return
        
        item = QTreeWidgetItem(parent_item)
        item.setText(0, node_data["name"])
        item.setData(0, Qt.ItemDataRole.UserRole, node_data["path"])
        
        if node_data["type"] == "directory":
            for child in node_data.get("children", []):
                self._build_tree(child, item)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Xử lý khi double click vào item"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isdir(path):
            self.path_edit.setText(path)
    
    def browse_folder(self):
        """Mở dialog chọn thư mục"""
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục", self.suggested_path
        )
        if folder:
            self.path_edit.setText(folder)
    
    def accept(self):
        """Xử lý khi nhấn OK"""
        self.selected_path = self.path_edit.text()
        if not self.selected_path:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thư mục đích")
            return
        
        if not os.path.exists(self.selected_path):
            reply = QMessageBox.question(
                self, "Xác nhận", 
                f"Thư mục '{self.selected_path}' không tồn tại. Tạo thư mục mới?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if not self.file_manager.create_directory_if_not_exists(self.selected_path):
                    QMessageBox.critical(self, "Lỗi", "Không thể tạo thư mục")
                    return
            else:
                return
        
        super().accept()
    
    def get_selected_path(self) -> str:
        """Trả về đường dẫn đã chọn"""
        return self.selected_path

class PMISAssistantUI(QMainWindow):
    """Giao diện chính của PMIS Assistant"""
    
    # Signal để thông báo cho main module
    save_completed = pyqtSignal()
    
    def __init__(self, clipboard_data: Dict[str, Any], ai_result: Dict[str, Any], 
                 db_manager: DatabaseManager, file_manager: FileManager):
        super().__init__()
        self.clipboard_data = clipboard_data
        self.ai_result = ai_result
        self.db_manager = db_manager
        self.file_manager = file_manager
        
        # Dữ liệu đã chọn từ tree view
        self.selected_columns = {}
        self.table_data = {}
        
        # Đường dẫn file gốc (nếu có)
        self.original_file_path = ""
        if clipboard_data.get("type") in ["file", "image"]:
            self.original_file_path = clipboard_data.get("content", "")
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Kết quả phân tích AI
        ai_group = self._create_ai_analysis_group()
        main_layout.addWidget(ai_group)
        
        # Thông tin file
        file_group = self._create_file_info_group()
        main_layout.addWidget(file_group)
        
        # Splitter cho tree view và bảng dữ liệu
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tree view (ẩn ban đầu)
        self.tree_container = self._create_tree_view_container()
        self.tree_container.hide()  # Ẩn ban đầu
        splitter.addWidget(self.tree_container)
        
        # Bảng dữ liệu (ẩn ban đầu)
        self.table_container = self._create_table_container()
        self.table_container.hide()  # Ẩn ban đầu
        splitter.addWidget(self.table_container)
        
        main_layout.addWidget(splitter)
        
        # Buttons
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
    
    def _create_ai_analysis_group(self) -> QGroupBox:
        """Tạo nhóm hiển thị kết quả phân tích AI"""
        group = QGroupBox("Kết quả phân tích Z.AI")
        layout = QVBoxLayout()
        
        # Tóm tắt nội dung
        summary_label = QLabel("Tóm tắt nội dung:")
        layout.addWidget(summary_label)
        
        self.summary_edit = QTextEdit()
        self.summary_edit.setMaximumHeight(100)
        self.summary_edit.setPlainText(self.ai_result.get("summary", ""))
        layout.addWidget(self.summary_edit)
        
        # Kết quả mapping
        mapping_label = QLabel("Mapping với CSDL:")
        layout.addWidget(mapping_label)
        
        self.mapping_edit = QTextEdit()
        self.mapping_edit.setMaximumHeight(150)
        mapping_text = self._format_mapping_result()
        self.mapping_edit.setPlainText(mapping_text)
        layout.addWidget(self.mapping_edit)
        
        group.setLayout(layout)
        return group
    
    def _create_file_info_group(self) -> QGroupBox:
        """Tạo nhóm thông tin file"""
        group = QGroupBox("Thông tin file")
        layout = QFormLayout()
        
        # Tên file đề xuất
        suggested_filename = self.file_manager.suggest_filename(
            self.ai_result, 
            os.path.basename(self.original_file_path) if self.original_file_path else ""
        )
        
        self.filename_edit = QLineEdit(suggested_filename)
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self.filename_edit)
        
        change_filename_button = QPushButton("Thay đổi")
        change_filename_button.clicked.connect(self.change_filename)
        filename_layout.addWidget(change_filename_button)
        
        layout.addRow("Tên file đề xuất:", filename_layout)
        
        # Vị trí lưu
        suggested_destination = self.file_manager.suggest_destination(self.ai_result)
        
        self.destination_edit = QLineEdit(suggested_destination)
        self.destination_edit.setReadOnly(True)
        
        destination_layout = QHBoxLayout()
        destination_layout.addWidget(self.destination_edit)
        
        change_dest_button = QPushButton("Thay đổi nơi đích")
        change_dest_button.clicked.connect(self.change_destination)
        destination_layout.addWidget(change_dest_button)
        
        layout.addRow("Vị trí lưu:", destination_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_tree_view_container(self) -> QWidget:
        """Tạo container cho tree view"""
        container = QWidget()
        layout = QVBoxLayout()
        
        # Header với buttons
        header_layout = QHBoxLayout()
        
        select_columns_button = QPushButton("Chọn bảng và cột")
        select_columns_button.clicked.connect(self.select_columns)
        header_layout.addWidget(select_columns_button)
        
        header_layout.addStretch()
        
        toggle_tree_button = QPushButton("Ẩn tree view")
        toggle_tree_button.clicked.connect(self.toggle_tree_view)
        header_layout.addWidget(toggle_tree_button)
        
        layout.addLayout(header_layout)
        
        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Bảng/Cột", "Kiểu dữ liệu"])
        layout.addWidget(self.tree_widget)
        
        container.setLayout(layout)
        return container
    
    def _create_table_container(self) -> QWidget:
        """Tạo container cho bảng dữ liệu"""
        container = QWidget()
        layout = QVBoxLayout()
        
        # Header với button
        header_layout = QHBoxLayout()
        
        show_tree_button = QPushButton("Hiện tree view")
        show_tree_button.clicked.connect(self.show_tree_view)
        header_layout.addWidget(show_tree_button)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_widget)
        
        # Filter row
        self.filter_row_widgets = []
        layout.addLayout(self._create_filter_row())
        
        container.setLayout(layout)
        return container
    
    def _create_filter_row(self) -> QHBoxLayout:
        """Tạo hàng filter cho bảng"""
        layout = QHBoxLayout()
        
        # Sẽ được tạo động sau khi có dữ liệu bảng
        self.filter_layout = layout
        
        return layout
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Tạo layout cho các button"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        cancel_button = QPushButton("Hủy")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button)
        
        save_button = QPushButton("Xác nhận và Lưu")
        save_button.clicked.connect(self.save_data)
        save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        layout.addWidget(save_button)
        
        return layout
    
    def _format_mapping_result(self) -> str:
        """Định dạng kết quả mapping để hiển thị"""
        mapping_results = self.ai_result.get("mapping_results", {})
        text_parts = []
        
        for table_name, result in mapping_results.items():
            if result.get("matched", False):
                confidence = result.get("confidence", 0.0)
                if table_name == "DuAn":
                    text_parts.append(f"Dự án: {result.get('project_name', '')} (Mã: {result.get('project_code', '')}) - Độ tin cậy: {confidence:.2f}")
                elif table_name == "PhongBan":
                    text_parts.append(f"Phòng ban: {result.get('department_name', '')} (Mã: {result.get('department_code', '')}) - Độ tin cậy: {confidence:.2f}")
                elif table_name == "CongViec":
                    text_parts.append(f"Công việc: {result.get('task_name', '')} - Độ tin cậy: {confidence:.2f}")
                elif table_name == "VanDe":
                    text_parts.append(f"Vấn đề: {result.get('issue_description', '')} - Độ tin cậy: {confidence:.2f}")
                elif table_name == "TienTrinhXuLy":
                    text_parts.append(f"Tiến trình: {result.get('progress_status', '')} - Độ tin cậy: {confidence:.2f}")
        
        return "\n".join(text_parts) if text_parts else "Không tìm thấy mapping phù hợp"
    
    def select_columns(self):
        """Hiển thị dialog chọn cột"""
        dialog = TableColumnSelectionDialog(self.db_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_columns = dialog.get_selected_columns()
            self._populate_table_with_selected_columns()
            self._show_table_container()
    
    def _populate_table_with_selected_columns(self):
        """Điền dữ liệu vào bảng với các cột đã chọn"""
        if not self.selected_columns:
            return
        
        try:
            # Lấy dữ liệu từ database
            all_data = {}
            for table_name, columns in self.selected_columns.items():
                data = self.db_manager.get_table_data(table_name, columns)
                all_data[table_name] = data
            
            # Hiển thị dữ liệu trong bảng
            self._display_data_in_table(all_data)
            
        except Exception as e:
            logger.error(f"Error populating table: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _display_data_in_table(self, data: Dict[str, List[Dict]]):
        """Hiển thị dữ liệu trong bảng"""
        # Gộp tất cả các cột từ các bảng
        all_columns = []
        for table_name, columns in self.selected_columns.items():
            for column in columns:
                all_columns.append(f"{table_name}.{column}")
        
        # Thiết lập số cột và hàng
        self.table_widget.setColumnCount(len(all_columns))
        self.table_widget.setHorizontalHeaderLabels(all_columns)
        
        # Tìm số hàng tối đa
        max_rows = 0
        table_data = {}
        for table_name, rows in data.items():
            table_data[table_name] = rows
            max_rows = max(max_rows, len(rows))
        
        self.table_widget.setRowCount(max_rows)
        
        # Điền dữ liệu
        for row in range(max_rows):
            col = 0
            for table_name, columns in self.selected_columns.items():
                rows = table_data.get(table_name, [])
                if row < len(rows):
                    row_data = rows[row]
                    for column in columns:
                        value = str(row_data.get(column, ""))
                        item = QTableWidgetItem(value)
                        self.table_widget.setItem(row, col, item)
                        col += 1
                else:
                    # Nếu không có dữ liệu cho hàng này, để trống
                    for _ in columns:
                        col += 1
        
        # Tạo filter row
        self._create_filter_widgets()
    
    def _create_filter_widgets(self):
        """Tạo các widget filter cho mỗi cột"""
        # Xóa các widget cũ
        for widget in self.filter_row_widgets:
            widget.deleteLater()
        self.filter_row_widgets.clear()
        
        # Tạo widget mới
        for col in range(self.table_widget.columnCount()):
            filter_edit = QLineEdit()
            filter_edit.setPlaceholderText("Filter...")
            filter_edit.textChanged.connect(self.filter_data)
            self.filter_layout.addWidget(filter_edit)
            self.filter_row_widgets.append(filter_edit)
    
    def filter_data(self):
        """Lọc dữ liệu trong bảng dựa trên các filter"""
        filters = {}
        for i, widget in enumerate(self.filter_row_widgets):
            if widget and widget.text().strip():
                filters[i] = widget.text().strip()
        
        if not filters:
            # Nếu không có filter, hiển thị tất cả các hàng
            for row in range(self.table_widget.rowCount()):
                self.table_widget.setRowHidden(row, False)
            return
        
        # Áp dụng filter
        for row in range(self.table_widget.rowCount()):
            show_row = True
            for col, filter_text in filters.items():
                item = self.table_widget.item(row, col)
                if item and filter_text.lower() not in item.text().lower():
                    show_row = False
                    break
            
            self.table_widget.setRowHidden(row, not show_row)
    
    def toggle_tree_view(self):
        """Ẩn/hiện tree view"""
        if self.tree_container.isVisible():
            self.tree_container.hide()
            if self.selected_columns:
                self.table_container.show()
        else:
            self.tree_container.show()
            self.table_container.hide()
    
    def show_tree_view(self):
        """Hiển thị tree view"""
        self.tree_container.show()
        self.table_container.hide()
    
    def _show_table_container(self):
        """Hiển thị container bảng"""
        self.tree_container.hide()
        self.table_container.show()
    
    def change_filename(self):
        """Thay đổi tên file"""
        # Có thể mở dialog để người dùng nhập tên file mới
        # Hiện tại chỉ cho phép chỉnh sửa trực tiếp
        self.filename_edit.setFocus()
    
    def change_destination(self):
        """Thay đổi nơi lưu file"""
        current_path = self.destination_edit.text()
        dialog = DestinationFolderDialog(self.file_manager, current_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = dialog.get_selected_path()
            self.destination_edit.setText(new_path)
    
    def save_data(self):
        """Lưu dữ liệu vào database và file"""
        try:
            # Lấy thông tin từ UI
            summary = self.summary_edit.toPlainText()
            filename = self.filename_edit.text()
            destination = self.destination_edit.text()
            
            # Validate
            if not filename:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên file")
                return
            
            if not destination:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn vị trí lưu")
                return
            
            # Validate tên file
            is_valid, error_msg = self.file_manager.validate_filename(filename)
            if not is_valid:
                QMessageBox.warning(self, "Lỗi", f"Tên file không hợp lệ: {error_msg}")
                return
            
            # Làm sạch tên file
            filename = self.file_manager.clean_filename(filename)
            
            # Xử lý file
            success, message = self._process_file(filename, destination)
            if not success:
                QMessageBox.critical(self, "Lỗi", message)
                return
            
            # Lưu vào database
            self._save_to_database(summary, filename, destination, message)
            
            # Log hoạt động AI
            self.db_manager.log_ai_activity(
                filename, 
                json.dumps(self.ai_result, ensure_ascii=False), 
                "success"
            )
            
            QMessageBox.information(self, "Thành công", "Dữ liệu đã được lưu thành công!")
            
            # Phát signal để thông báo cho main module
            self.save_completed.emit()
            
            # Đóng cửa sổ
            self.close()
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi lưu dữ liệu: {str(e)}")
    
    def _process_file(self, filename: str, destination: str) -> Tuple[bool, str]:
        """Xử lý file (di chuyển hoặc sao chép)"""
        if self.original_file_path and os.path.exists(self.original_file_path):
            # Di chuyển file gốc
            if self.clipboard_data.get("type") == "file":
                return self.file_manager.move_file(self.original_file_path, destination, filename)
            else:
                # Sao chép file (đối với ảnh từ clipboard)
                return self.file_manager.copy_file(self.original_file_path, destination, filename)
        else:
            # Tạo file từ text
            text_content = self.clipboard_data.get("content", "")
            return self.file_manager.save_text_to_file(text_content, destination, filename)
    
    def _save_to_database(self, summary: str, filename: str, destination: str, file_path: str):
        """Lưu thông tin vào database"""
        # Lưu vào bảng tbl_documents
        document_data = {
            "file_name": filename,
            "doc_type": self.ai_result.get("document_info", {}).get("document_type_name", ""),
            "doc_date": self.ai_result.get("document_info", {}).get("date"),
            "project_name": self.ai_result.get("mapping_results", {}).get("DuAn", {}).get("project_name", ""),
            "sender": self.ai_result.get("document_info", {}).get("issuing_authority", ""),
            "receiver": "",
            "summary": summary,
            "keywords": self.ai_result.get("keywords", []),
            "raw_content": self.clipboard_data.get("content", ""),
            "ai_analysis_json": json.dumps(self.ai_result, ensure_ascii=False),
            "file_path_original": file_path
        }
        
        doc_id = self.db_manager.insert_into_documents_table(document_data)
        
        # Lưu vào bảng nghiệp vụ tương ứng (nếu có mapping)
        self._save_to_business_table(doc_id)
        
        return doc_id
    
    def _save_to_business_table(self, doc_id: int):
        """Lưu vào bảng nghiệp vụ tương ứng"""
        mapping_results = self.ai_result.get("mapping_results", {})
        
        # Lưu vào VanBanPhapLy nếu có thông tin văn bản
        if mapping_results.get("DuAn", {}).get("matched", False):
            doc_info = self.ai_result.get("document_info", {})
            if doc_info.get("document_number") or doc_info.get("ngay_ban_hanh"):
                van_ban_data = {
                    "DuAn_ID": mapping_results.get("DuAn", {}).get("project_id"),
                    "SoHieu": doc_info.get("document_number", ""),
                    "NoiDung": self.ai_result.get("summary", ""),
                    "NgayBanHanh": doc_info.get("date")
                }
                self.db_manager.insert_document("VanBanPhapLy", van_ban_data)
        
        # Có thể mở rộng để lưu vào các bảng nghiệp vụ khác
        # dựa trên kết quả mapping

def show_ui(clipboard_data: Dict[str, Any], ai_result: Dict[str, Any], 
            db_manager: DatabaseManager, file_manager: FileManager) -> int:
    """Hiển thị UI và trả về kết quả"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = PMISAssistantUI(clipboard_data, ai_result, db_manager, file_manager)
    window.show()
    
    # Chạy event loop
    return app.exec()