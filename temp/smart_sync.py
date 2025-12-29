import pandas as pd
from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal, InvalidOperation
from sqlalchemy.types import Numeric
import os
import sys
import urllib.parse
import platform
import logging

# ============================================================
# 1. CẤU HÌNH HỆ THỐNG (GIỮ NGUYÊN NHƯ CŨ)
# ============================================================

CURRENT_OS = platform.system()

if CURRENT_OS == 'Windows':
    # --- CẤU HÌNH KHI CHẠY TRÊN MÁY TÍNH (WINDOWS) ---
    logging.basicConfig(filename='smart_sync.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger(__name__)
    
    # Log ra màn hình để xem
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)

    # === [ĐOẠN CỐT LÕI MỚI SỬA] ===
    # Lấy tên máy tính hiện tại (Ví dụ: PC-on-NAS, Laptop-Khoi...)
    computer_name = platform.node()
    
    # So sánh tên máy (chuyển về chữ hoa để so sánh cho chính xác)
    if computer_name.upper() == 'PC-ON-NAS':
        # Trường hợp 1: Chạy trên máy ảo NAS
        logger.info(f'>> Phát hiện máy ảo: {computer_name} -> Dùng IP LAN nội bộ')
        DB_HOST = '192.168.1.8'  # IP của NAS trong mạng LAN
    else:
        # Trường hợp 2: Chạy trên Laptop ở xa (quán Cafe, ở nhà...)
        logger.info(f'>> Phát hiện máy từ xa: {computer_name} -> Dùng IP Tailscale')
        DB_HOST = '100.94.213.83' # IP Tailscale
    
    # Đường dẫn Excel trên Windows (cả 2 máy đều map ổ Z giống nhau)
    EXCEL_PATH = r'Z:\PMIS.VP\PMIS.VP.xlsx' 
    # ===============================
    
else:
    # --- CẤU HÌNH KHI CHẠY TRÊN NAS (LINUX) ---
    logging.basicConfig(filename='smart_sync.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger(__name__)
    # also log to console so user can see progress when running interactively
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)
    logger.info('>> Đang chạy trên: NAS/LINUX (Chạy trực tiếp)')
    DB_HOST = 'localhost'
    
    _nas_candidates = [
        r'/volume3/Onedriver VPI/PMIS.VP/PMIS.VP.xlsx',
        r'/volume3/Onedriver VPI/PMIS.VP.xlsx',
        r'/volume1/Onedriver VPI/PMIS.VP/PMIS.VP.xlsx',
        r'/volume1/Onedriver VPI/PMIS.VP.xlsx',
        r'/volume3/PMIS.VP.xlsx',
    ]
    EXCEL_PATH = None
    for p in _nas_candidates:
        if os.path.exists(p):
            EXCEL_PATH = p
            break
    if EXCEL_PATH is None:
        EXCEL_PATH = _nas_candidates[0]

# --- QUAN TRỌNG: KHÔI PHỤC LẠI PORT 2345 CỦA BẠN ---
DB_PORT = '2345'                
DB_USER = 'postgres'
DB_NAME = 'PMIS'
DB_PASS = 'O*&-Unh-LNG-%^#'     

# ============================================================
# 2. MÔ HÌNH VALIDATION (PYDANTIC)
# ============================================================
def normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in list(df.columns):
        if 'ngay' in col.lower() or 'date' in col.lower():
            try:
                df[col] = df[col].apply(lambda v: None if pd.isna(v) or v == '' else pd.to_datetime(v).date())
            except Exception:
                df[col] = df[col].apply(lambda v: None)
    return df

# ============================================================
# 3. THỨ TỰ NẠP BẢNG & LUẬT XÓA LAN TRUYỀN (MỚI)
# ============================================================
ORDERED_TABLES = [
    'PhongBan', 'CongTy', 'NhomMucTieu', 'ChuKy', 'CanCuPhapLy',
    'NhanSu', 'DuAn', 'MucTieu',
    'CongViec', 'GoiThau', 'VanBanPhapLy', 'VanDe',
    'HopDong', 'TienTrinhXuLy', 'PhanCongNhanSu', 'PhanCongMucTieu'
]

# [PHẦN MỚI THÊM VÀO] Định nghĩa quan hệ để xóa lan truyền
ORPHAN_CLEANUP_RULES = {
    'CongViec': ('DuAn_ID', 'DuAn'),
    'GoiThau': ('DuAn_ID', 'DuAn'),
    'VanDe': ('DuAn_ID', 'DuAn'),
    'VanBanPhapLy': ('DuAn_ID', 'DuAn'),
    'HopDong': ('GoiThau_ID', 'GoiThau'),
    'TienTrinhXuLy': ('CongViec_ID', 'CongViec'), # Case ID 5 của bạn sẽ được xử lý ở đây
    'PhanCongNhanSu': ('CongViec_ID', 'CongViec'),
    'PhanCongMucTieu': ('MucTieu_ID', 'MucTieu')
}

# ============================================================
# 4. HÀM XỬ LÝ CHÍNH
# ============================================================

def get_engine():
    safe_pass = urllib.parse.quote_plus(DB_PASS)
    conn_str = f"postgresql+psycopg2://{DB_USER}:{safe_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(conn_str)

def clean_dataframe(df):
    df = df.where(pd.notnull(df), None)
    df = normalize_date_columns(df)
    if 'is_deleted' not in df.columns:
        df['is_deleted'] = False
    else:
        df['is_deleted'] = df['is_deleted'].fillna(False)
    df['last_updated'] = datetime.now()
    return df

# [PHẦN MỚI THÊM VÀO] Hàm thực hiện xóa logic
def cleanup_orphans(engine):
    logger.info("--- BƯỚC PHỤ: DỌN DẸP DỮ LIỆU MỒ CÔI (CASCADING SOFT DELETE) ---")
    with engine.begin() as conn: 
        for child_table, (fk_col, parent_table) in ORPHAN_CLEANUP_RULES.items():
            try:
                # Tìm các dòng con chưa xóa (false) nhưng có cha đã xóa (true) -> Update thành true
                sql = text(f"""
                    UPDATE "{child_table}"
                    SET is_deleted = true, last_updated = NOW()
                    WHERE is_deleted = false 
                    AND "{fk_col}" IN (
                        SELECT "ID" FROM "{parent_table}" WHERE is_deleted = true
                    );
                """)
                result = conn.execute(sql)
                if result.rowcount > 0:
                    logger.info(f"   -> [Auto-Clean] Đã xóa mềm {result.rowcount} dòng trong '{child_table}' vì cha bên '{parent_table}' đã bị xóa.")
            except Exception as e:
                logger.warning(f"   [Cảnh báo Cleanup {child_table}]: {e}")

def sync_upsert_soft_delete():
    logger.info("--- BẮT ĐẦU ĐỒNG BỘ DỮ LIỆU (UPSERT & SOFT DELETE) ---")
    logger.info(f">> File Excel: {EXCEL_PATH}")
    logger.info(f">> Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    if not os.path.exists(EXCEL_PATH):
        logger.error(f"[LỖI] Không tìm thấy file Excel tại {EXCEL_PATH}.")
        return

    try:
        engine = get_engine()
        metadata = MetaData()
        metadata.reflect(bind=engine)
        logger.info(">> Kết nối Database thành công!")
    except Exception as e:
        logger.error(f"[LỖI KẾT NỐI DB]: {e}")
        return
    
    try:
        logger.info(">> Đang đọc file Excel...")
        all_sheets = pd.read_excel(EXCEL_PATH, sheet_name=None, engine='openpyxl')
    except Exception as e:
        logger.error(f"[LỖI ĐỌC EXCEL]: {e}")
        return

    # Logic đồng bộ chính (Giữ nguyên của bạn)
    with engine.connect() as conn:
        for table_name in ORDERED_TABLES:
            if table_name not in all_sheets: continue

            logger.info(f"Đang xử lý bảng: {table_name}")
            df = all_sheets[table_name]
            if df.empty:
                logger.info("   (Bảng trống)")
                continue
            
            try:
                table_obj = Table(table_name, metadata, autoload_with=engine)
                pk_col = list(table_obj.primary_key.columns)[0].name 
            except Exception as e:
                logger.error(f"   [!] Lỗi bảng '{table_name}': {e}")
                continue

            df = clean_dataframe(df)
            db_cols = [c.name for c in table_obj.columns]
            valid_cols = [c for c in df.columns if c in db_cols]
            df = df[valid_cols]

            # Xử lý Numeric/Decimal
            numeric_cols = []
            for col_obj in table_obj.columns:
                if isinstance(col_obj.type, Numeric):
                    numeric_cols.append((col_obj.name, getattr(col_obj.type, 'scale', None)))
            if numeric_cols:
                for col_name, scale in numeric_cols:
                    if col_name in df.columns:
                        def to_decimal(v):
                            if v is None: return None
                            try:
                                d = Decimal(str(v))
                                if scale is not None:
                                    q = Decimal((0, (1,), -scale)) if scale > 0 else Decimal(1)
                                    return d.quantize(q)
                                return d
                            except: return None
                        df[col_name] = df[col_name].apply(to_decimal)

            # Xử lý Integer
            from sqlalchemy.types import Integer
            # Thay applymap (bị deprecated) bằng where để thay NaN thành None
            df = df.where(pd.notnull(df), None)
            int_cols = [c.name for c in table_obj.columns if isinstance(c.type, Integer)]
            for col in int_cols:
                if col in df.columns:
                    def to_int(v):
                        try: return int(v)
                        except: return None
                    df[col] = df[col].apply(to_int)

            # 1. Soft Delete từ Excel
            try:
                existing_ids_query = text(f'SELECT "{pk_col}" FROM "{table_name}"')
                existing_ids_df = pd.read_sql(existing_ids_query, conn)
                existing_ids = set(existing_ids_df[pk_col].tolist())
                excel_ids = set(df[pk_col].dropna().tolist())
                ids_to_soft_delete = list(existing_ids - excel_ids)
                
                if ids_to_soft_delete:
                    logger.info(f"   -> Phát hiện {len(ids_to_soft_delete)} dòng bị xóa khỏi Excel. Update is_deleted=True.")
                    update_stmt = (
                        table_obj.update()
                        .where(table_obj.c[pk_col].in_(ids_to_soft_delete))
                        .values(is_deleted=True, last_updated=datetime.now())
                    )
                    conn.execute(update_stmt)
                    conn.commit()
            except Exception as e: print(f"   [Cảnh báo Soft Delete]: {e}")

            # 2. Upsert
            raw_records = df.to_dict(orient='records')
            records = []
            numeric_col_names = {name for name, _ in numeric_cols}
            int_col_names = set(int_cols)

            for r in raw_records:
                clean_r = {}
                for k, v in r.items():
                    if pd.isna(v): clean_r[k] = None; continue
                    try: 
                        if hasattr(v, 'item'): v = v.item()
                    except: pass
                    
                    if k in int_col_names:
                        try: clean_r[k] = int(v)
                        except: clean_r[k] = None
                        continue
                    if k in numeric_col_names:
                        try:
                            d = Decimal(str(v))
                            scale = next((s for name, s in numeric_cols if name == k), None)
                            if scale is not None:
                                q = Decimal((0, (1,), -scale)) if scale > 0 else Decimal(1)
                                d = d.quantize(q)
                            clean_r[k] = d
                        except: clean_r[k] = None
                        continue
                    clean_r[k] = v
                records.append(clean_r)
            
            logger.info(f"   -> Đang đồng bộ {len(records)} dòng...")
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                if not batch: continue
                insert_stmt = insert(table_obj).values(batch)
                update_dict = {col: getattr(insert_stmt.excluded, col) for col in valid_cols if col != pk_col}
                upsert_stmt = insert_stmt.on_conflict_do_update(index_elements=[pk_col], set_=update_dict)
                try:
                    conn.execute(upsert_stmt)
                    conn.commit()
                except Exception as e:
                    logger.error(f"   [LỖI BATCH]: {e}")
                    conn.rollback()

    # [PHẦN MỚI THÊM VÀO] Gọi hàm dọn dẹp sau khi xong hết
    cleanup_orphans(engine)

    logger.info("--- ĐỒNG BỘ HOÀN TẤT 100% ---")

if __name__ == "__main__":
    sync_upsert_soft_delete()