import win32com.client
import pandas as pd
import os
from pathlib import Path
import datetime
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# --- CẤU HÌNH ---
WORK_DIR = r"Y:\00_Landing Zone" # Thay đổi đường dẫn này nếu cần

# --- HÀM XỬ LÝ QUAN HỆ CHA CON ---
def add_parent_child_columns(df):
    """
    Hàm này thêm cột Parent_ID và Parent_Name dựa trên OutlineLevel
    """
    # Vì dữ liệu xuất ra là string, cần tạo cột tạm dạng số để tính toán logic
    df['temp_Level'] = pd.to_numeric(df['OutlineLevel'], errors='coerce')
    
    # Dictionary lưu ID của level gần nhất đang duyệt
    last_seen_level_id = {}
    parent_ids = []

    # Duyệt qua từng dòng
    for index, row in df.iterrows():
        # Bỏ qua nếu dòng lỗi không có level
        if pd.isna(row['temp_Level']):
            parent_ids.append(None)
            continue

        current_level = int(row['temp_Level'])
        current_id = row['ID'] 
        
        # Lưu ID của level hiện tại
        last_seen_level_id[current_level] = current_id
        
        # Tìm cha: Cha là Level hiện tại - 1
        parent_level = current_level - 1
        
        if parent_level in last_seen_level_id and parent_level > 0:
            parent_ids.append(last_seen_level_id[parent_level])
        else:
            parent_ids.append(None)

    # Gán cột Parent_ID mới
    df['Parent_ID'] = parent_ids
    
    # Map để lấy tên Parent Name cho dễ nhìn
    # Cần kiểm tra xem cột Name có tồn tại không, nếu không thì chỉ để ID
    if 'Name' in df.columns:
        id_name_map = dict(zip(df['ID'], df['Name']))
        df['Parent_Name'] = df['Parent_ID'].map(id_name_map)
    else:
        df['Parent_Name'] = "" # Nếu view không có cột Name thì để trống
    
    # Xóa cột tạm dùng để tính toán
    df.drop(columns=['temp_Level'], inplace=True)
    
    return df


def normalize_duration_to_days(duration_value):
    """Convert MS Project Duration to working days.

    Requirement: divide by 480 and round to 0 decimals before exporting to Excel.
    This function is defensive because Duration may come as a number or a formatted string.
    """
    if duration_value is None:
        return ""

    if isinstance(duration_value, (int, float)):
        minutes_str = str(duration_value)
    else:
        duration_str = str(duration_value).strip()
        if duration_str == "":
            return ""
        match = re.search(r"[-+]?\d*\.?\d+", duration_str)
        if not match:
            return duration_str
        minutes_str = match.group(0)

    try:
        minutes = Decimal(minutes_str)
        days = minutes / Decimal("480")
        rounded_days = int(days.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return rounded_days
    except (InvalidOperation, ZeroDivisionError, ValueError):
        return str(duration_value)

# --- HÀM CHÍNH ---
def batch_convert_mpp_to_excel_dynamic():
    # 1. Kiểm tra thư mục
    folder_path = Path(WORK_DIR)
    if not folder_path.exists():
        print(f"❌ Lỗi: Thư mục '{WORK_DIR}' không tồn tại!")
        return

    # Lấy danh sách tất cả file .mpp
    mpp_files = list(folder_path.glob("*.mpp"))
    
    if not mpp_files:
        print(f"⚠️ Không tìm thấy file .mpp nào trong '{WORK_DIR}'")
        return

    print(f"📂 Tìm thấy {len(mpp_files)} file MS Project. Bắt đầu xử lý...\n")

    # 2. Khởi động MS Project
    try:
        mpp_app = win32com.client.Dispatch("MSProject.Application")
        mpp_app.Visible = False      
        mpp_app.DisplayAlerts = False 
    except Exception as e:
        print("❌ Lỗi: Không thể khởi động MS Project.")
        print(f"Chi tiết: {e}")
        return

    # 3. Duyệt qua từng file và xử lý
    for mpp_file in mpp_files:
        try:
            print(f"➡️ Đang đọc: {mpp_file.name}...")
            
            mpp_app.FileOpen(str(mpp_file))
            project = mpp_app.ActiveProject

            # --- TỰ ĐỘNG LẤY DANH SÁCH CỘT ĐANG HIỂN THỊ ---
            current_columns = []
            
            # Lấy bảng hiện tại (Current Table)
            try:
                active_table = project.TaskTables(project.CurrentTable)
                
                # Duyệt qua các trường trong bảng để lấy tên cột
                for field in active_table.TableFields:
                    try:
                        # Chuyển Field Constant (số) sang tên thuộc tính (chuỗi) -> ví dụ: "Start", "Finish"
                        field_name = mpp_app.FieldConstantToFieldName(field.Field)
                        if field_name:
                            current_columns.append(field_name)
                    except:
                        continue
            except Exception as col_err:
                print(f"   ⚠️ Cảnh báo: Không lấy được view động, dùng mặc định. Lỗi: {col_err}")
                current_columns = ['ID', 'Name', 'Duration', 'Start', 'Finish', 'PercentComplete']

            # --- ĐẢM BẢO LUÔN CÓ CÁC CỘT QUAN TRỌNG (ID & OUTLINELEVEL) ---
            # Để phục vụ việc tính toán cha con
            if 'ID' not in current_columns:
                current_columns.insert(0, 'ID') # Thêm ID vào đầu
            
            if 'OutlineLevel' not in current_columns:
                current_columns.append('OutlineLevel') # Thêm Level vào danh sách cần lấy
            
            # Loại bỏ cột trùng lặp (nếu có) nhưng giữ thứ tự
            unique_columns = []
            for col in current_columns:
                if col not in unique_columns:
                    unique_columns.append(col)
            
            print(f"   ℹ️ Số lượng cột sẽ xuất: {len(unique_columns)}")

            # --- TRÍCH XUẤT DỮ LIỆU ---
            data = []
            for task in project.Tasks:
                if task: 
                    row = {}
                    for col in unique_columns:
                        try:
                            val = getattr(task, col)
                            if isinstance(val, datetime.datetime):
                                val = val.strftime('%d/%m/%Y')
                            # Xử lý trường hợp None
                            if val is None:
                                val = ""

                            if col == 'Duration':
                                row[col] = normalize_duration_to_days(val)
                            else:
                                row[col] = str(val)
                        except:
                            row[col] = "" # Nếu cột lỗi hoặc không có dữ liệu
                    data.append(row)

            mpp_app.FileClose(1) 

            # 4. Lưu ra Excel
            excel_filename = mpp_file.with_suffix('.xlsx')
            
            df = pd.DataFrame(data)

            if not df.empty:
                print("   ...Đang xử lý phân cấp Cha-Con...")
                df = add_parent_child_columns(df)
            
            # Sắp xếp lại cột: Đưa Parent_ID, Parent_Name lên gần cột Name cho dễ nhìn (nếu muốn)
            # Ở đây tôi giữ nguyên append vào cuối cho an toàn.

            df.to_excel(excel_filename, index=False)
            
            print(f"✅ Đã lưu xong: {excel_filename.name}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý file {mpp_file.name}: {e}")
            try: mpp_app.FileClose(1)
            except: pass

    mpp_app.Quit()
    print("\n🎉 Hoàn thành tất cả công việc!")

if __name__ == "__main__":
    batch_convert_mpp_to_excel_dynamic()