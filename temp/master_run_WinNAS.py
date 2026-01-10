import os
import subprocess
import sys

# --- CẤU HÌNH ---
# 1. Đường dẫn thư mục chứa code (Lấy luôn thư mục hiện tại chứa file này)
CODE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Đường dẫn Python trong môi trường ảo (Trên máy ảo)
# Nếu bạn chạy trên máy thật thì sửa lại đường dẫn này, còn trên máy ảo thì giữ nguyên
VENV_PYTHON = r"C:\Code\pmis_env\Scripts\python.exe"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_py_files():
    """Tìm tất cả các file .py trong thư mục trừ file này ra"""
    files = [f for f in os.listdir(CODE_DIR) if f.endswith('.py') and f != os.path.basename(__file__)]
    return sorted(files)

def run_script(script_name):
    script_path = os.path.join(CODE_DIR, script_name)
    print(f"\n--------------------------------------------------")
    print(f"   DANG CHAY: {script_name}")
    print(f"--------------------------------------------------\n")
    
    try:
        # Gọi Python của môi trường ảo để chạy file con
        subprocess.run([VENV_PYTHON, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[LOI] Code gap su co (Ma loi: {e.returncode})")
    except FileNotFoundError:
        print(f"\n[LOI] Khong tim thay moi truong Python tai: {VENV_PYTHON}")
        print("Hay kiem tra lai xem da tao env o o C tren may nay chua!")
    
    print(f"\n--------------------------------------------------")
    input("   An Enter de quay lai Menu...")

def main():
    while True:
        clear_screen()
        print("==================================================")
        print("         HE THONG QUAN LY CODE PMIS")
        print("==================================================")
        
        py_files = get_py_files()
        
        if not py_files:
            print(" [!] Khong tim thay file .py nao trong thu muc nay!")
            input(" An Enter de thoat...")
            break

        # In danh sách menu
        print(f" Danh sach file code tai: {CODE_DIR}\n")
        for i, f in enumerate(py_files, 1):
            print(f"  [{i}] {f}")
            
        print("\n  [0] Thoat chuong trinh")
        print("==================================================")
        
        choice = input(">> Nhap so ban muon chay: ")
        
        if choice == '0':
            print("Tam biet!")
            break
            
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(py_files):
                run_script(py_files[idx])
            else:
                input("\n[!] So khong hop le! An Enter de chon lai...")
        else:
            input("\n[!] Vui long chi nhap so! An Enter de chon lai...")

if __name__ == "__main__":
    main()