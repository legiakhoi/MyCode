import os
import json

# ĐƯỜNG DẪN GỐC CỦA BẠN
root_path = r"C:\Users\legia\OneDrive - vanphu.vn\BAN KẾ HOẠCH - D7\00_KE HOACH KPI\04. DA BDS\01BNI005 - Phong Khe"

def scan_directory_structure(path):
    """
    Quét thư mục và tạo cấu trúc dictionary:
    {
        "Đường dẫn đầy đủ": ["từ khóa gợi ý 1", "từ khóa gợi ý 2"]
    }
    """
    folder_map = {}
    
    # Duyệt qua cây thư mục
    for dirpath, dirnames, filenames in os.walk(path):
        # Bỏ qua chính thư mục gốc nếu không muốn chứa file
        if dirpath == path:
            continue
            
        # Lấy tên thư mục cuối cùng để làm từ khóa gợi ý ban đầu
        folder_name = os.path.basename(dirpath)
        
        # Tạo danh sách từ khóa (bạn sẽ sửa lại list này sau)
        # Mặc định tôi để tên thư mục làm từ khóa đầu tiên
        keywords = [folder_name.lower()] 
        
        folder_map[dirpath] = keywords

    return folder_map

def save_structure_to_json(data, filename="folder_map.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Đã tạo thành công file cấu hình: {filename}")
        print("Vui lòng mở file này lên và thêm các từ khóa nhận diện cho từng thư mục!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# --- THỰC THI ---
if os.path.exists(root_path):
    structure = scan_directory_structure(root_path)
    save_structure_to_json(structure)
else:
    print(f"❌ Không tìm thấy đường dẫn: {root_path}")