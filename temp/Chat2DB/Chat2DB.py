import psycopg2
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv # Thêm dòng này

# 1. CẤU HÌNH GEMINI AI........máy cơ quan
# 1. Nạp key từ file .env lên
load_dotenv()

# 2. Lấy key ra sử dụng (Thay vì điền trực tiếp key vào đây)
# Nếu không tìm thấy key, nó sẽ trả về None
api_key = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY = ""
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=GEMINI_API_KEY)
print("✅ Đã kết nối Gemini AI!")

# 2. KẾT NỐI TRỰC TIẾP VÀO POSTGRESQL
print("Đang kết nối đến database...")
try:
    conn = psycopg2.connect(
        host='100.94.213.83',
        dbname='PMIS',
        user='postgres',
        password='O*&-Unh-LNG-%^#',
        port=2345
    )
    cursor = conn.cursor()
    print("✅ Kết nối đến database PMIS thành công!")
except Exception as e:
    print(f"❌ Lỗi kết nối: {str(e)}")
    exit(1)

# 3. LẤY THÔNG TIN SCHEMA ĐỂ TẠO CONTEXT CHO AI
print("\nĐang tải thông tin bảng...")
try:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📊 Tìm thấy {len(tables)} bảng: {', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")
    
    # Lấy thông tin chi tiết các cột của từng bảng
    schema_info = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        schema_info[table] = columns
    
    print("✅ Đã tải schema database!")
except Exception as e:
    print(f"⚠ Không thể lấy schema: {str(e)}")
    tables = []
    schema_info = {}

print("✅ Hệ thống sẵn sàng!")

# 4. HÀM TẠO SQL TỪ CÂU HỎI BẰNG GEMINI
def generate_sql_with_gemini(question):
    """Sử dụng Gemini AI để tạo SQL từ câu hỏi tiếng Việt"""
    
    # Tạo prompt với thông tin schema chi tiết
    schema_text = "CẤU TRÚC DATABASE POSTGRESQL:\n\n"
    for table, columns in schema_info.items():
        schema_text += f'Bảng: "{table}"\n'
        for col_name, col_type in columns:
            schema_text += f'  - "{col_name}" (kiểu: {col_type})\n'
        schema_text += "\n"
    
    prompt = f"""Bạn là chuyên gia SQL PostgreSQL. Hãy viết câu SQL trả lời câu hỏi tiếng Việt.

{schema_text}

QUY TẮC QUAN TRỌNG:
1. PHẢI bọc tất cả tên bảng và cột trong dấu ngoặc kép "" (vì PostgreSQL phân biệt chữ hoa/thường)
2. Tên bảng/cột phải CHÍNH XÁC như trong schema
3. Chỉ trả về MỘT câu SQL duy nhất, không giải thích
4. KHÔNG dùng markdown (```sql hoặc ```)
5. Với câu hỏi "ai có nhiều nhất":
   - Dùng COUNT, GROUP BY, ORDER BY ... DESC LIMIT 1
6. Với câu hỏi "ai ... và số lượng là bao nhiêu":
   - SELECT cả tên và COUNT trong cùng một câu
   - Dùng GROUP BY
7. Với câu hỏi đếm: COUNT(*)
8. Với câu hỏi liệt kê: SELECT * với LIMIT hợp lý

VÍ DỤ MẪU:
Hỏi: "Nhân sự nào có nhiều công việc nhất?"
→ SELECT "HoTen", COUNT(*) as "SoCongViec" FROM "NhanSu" JOIN "PhanCongNhanSu" ON "NhanSu"."ID" = "PhanCongNhanSu"."NhanSu_ID" GROUP BY "HoTen" ORDER BY COUNT(*) DESC LIMIT 1

Hỏi: "Có bao nhiêu dự án?"
→ SELECT COUNT(*) FROM "DuAn"

CÂU HỎI: {question}

Trả về ĐÚNG MỘT câu SQL (nhớ dùng dấu ngoặc kép):"""
    
    try:
        response = llm.invoke(prompt)
        
        # Xử lý response - có thể là object hoặc list
        if isinstance(response, list):
            sql = response[0].content.strip() if response else ""
        elif hasattr(response, 'content'):
            sql = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
        else:
            sql = str(response).strip()
        
        # Loại bỏ markdown nếu có
        if '```' in sql:
            # Tách ra các dòng
            lines = sql.split('\n')
            sql_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (line.strip() and not line.strip().startswith('#')):
                    sql_lines.append(line)
            sql = '\n'.join(sql_lines).strip()
        
        # Loại bỏ các dòng comment và chỉ giữ lại câu SQL
        if '\n' in sql:
            for line in sql.split('\n'):
                line = line.strip()
                if line and not line.startswith('--') and not line.startswith('#'):
                    if any(line.upper().startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
                        sql = line
                        break
        
        # Kiểm tra tính hợp lệ
        if not sql or 'ERROR' in sql.upper() or len(sql) < 10:
            return None
        
        return sql
    except Exception as e:
        print(f"⚠️ Lỗi Gemini: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 5. HÀM THỰC THI SQL TRỰC TIẾP
def run_sql_direct(sql_query):
    """Chạy SQL trực tiếp trên database và trả về DataFrame"""
    try:
        cursor.execute(sql_query)
        
        # Kiểm tra xem có kết quả trả về không
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            df = pd.DataFrame(results, columns=columns)
            return df
        else:
            conn.commit()
            return pd.DataFrame({"status": ["Query executed successfully"]})
    except Exception as e:
        conn.rollback()
        raise Exception(f"SQL Error: {str(e)}")

# 6. HỎI ĐÁP
print("\n" + "="*60)
print("💬 CHAT2DB - Hỏi đáp cơ sở dữ liệu PMIS (Powered by Gemini AI)")
print("="*60)
print("Bạn có thể:")
print("  1. Hỏi bằng tiếng Việt (AI sẽ tạo SQL)")
print("  2. Nhập SQL trực tiếp (bắt đầu bằng SELECT, INSERT, UPDATE, DELETE)")
print("  3. Gõ 'tables' để xem danh sách bảng")
print("  4. Gõ 'exit' để thoát")
print("="*60)

while True:
    question = input("\n❓ Câu hỏi của bạn: ").strip()
    
    if question.lower() == 'exit':
        print("👋 Tạm biệt!")
        break
    
    if question.lower() == 'tables':
        print(f"\n📋 Danh sách bảng ({len(tables)} bảng):")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        continue
    
    if not question:
        continue
    
    # Kiểm tra xem có phải SQL trực tiếp không
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'ALTER', 'DROP']
    is_direct_sql = any(question.upper().startswith(keyword) for keyword in sql_keywords)
    
    try:
        if is_direct_sql:
            # Chạy SQL trực tiếp
            print("⚙️ Đang thực thi SQL...")
            df = run_sql_direct(question)
            
            if not df.empty:
                print("\n✅ Kết quả:")
                print(df.to_string(index=False, max_rows=50, max_cols=20))
                print(f"\n📊 Tổng số dòng: {len(df)}")
            else:
                print("✅ Truy vấn thành công nhưng không có dữ liệu.")
        else:
            # Dùng Gemini AI để tạo SQL
            print("🤖 Gemini AI đang tạo SQL từ câu hỏi...")
            
            sql = generate_sql_with_gemini(question)
            
            if sql and isinstance(sql, str) and len(sql.strip()) > 0:
                print(f"\n📝 SQL được tạo:\n{sql}\n")
                
                # Chạy SQL
                print("⚙️ Đang thực thi...")
                df = run_sql_direct(sql)
                
                if not df.empty:
                    print("\n✅ Kết quả:")
                    print(df.to_string(index=False, max_rows=50, max_cols=20))
                    print(f"\n📊 Tổng số dòng: {len(df)}")
                else:
                    print("⚠️ Truy vấn không trả về dữ liệu.")
            else:
                print("⚠️ Gemini AI không thể tạo SQL. Hãy thử:")
                print("  - Diễn đạt lại câu hỏi rõ ràng hơn")
                print("  - Hoặc nhập SQL trực tiếp")
                
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        print("💡 Vui lòng kiểm tra lại câu hỏi hoặc SQL của bạn.")

# Đóng kết nối
cursor.close()
conn.close()
print("\n✅ Đã đóng kết nối database.")
import psycopg2
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# 1. CẤU HÌNH GEMINI AI
GEMINI_API_KEY = ""
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=GEMINI_API_KEY)
print("✅ Đã kết nối Gemini AI!")

# 2. KẾT NỐI TRỰC TIẾP VÀO POSTGRESQL
print("Đang kết nối đến database...")
try:
    conn = psycopg2.connect(
        host='100.94.213.83',
        dbname='PMIS',
        user='postgres',
        password='O*&-Unh-LNG-%^#',
        port=2345
    )
    cursor = conn.cursor()
    print("✅ Kết nối đến database PMIS thành công!")
except Exception as e:
    print(f"❌ Lỗi kết nối: {str(e)}")
    exit(1)

# 3. LẤY THÔNG TIN SCHEMA ĐỂ TẠO CONTEXT CHO AI
print("\nĐang tải thông tin bảng...")
try:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📊 Tìm thấy {len(tables)} bảng: {', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")
    
    # Lấy thông tin chi tiết các cột của từng bảng
    schema_info = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        schema_info[table] = columns
    
    print("✅ Đã tải schema database!")
except Exception as e:
    print(f"⚠ Không thể lấy schema: {str(e)}")
    tables = []
    schema_info = {}

print("✅ Hệ thống sẵn sàng!")

# 4. HÀM TẠO SQL TỪ CÂU HỎI BẰNG GEMINI
def generate_sql_with_gemini(question):
    """Sử dụng Gemini AI để tạo SQL từ câu hỏi tiếng Việt"""
    
    # Tạo prompt với thông tin schema chi tiết
    schema_text = "CẤU TRÚC DATABASE POSTGRESQL:\n\n"
    for table, columns in schema_info.items():
        schema_text += f'Bảng: "{table}"\n'
        for col_name, col_type in columns:
            schema_text += f'  - "{col_name}" (kiểu: {col_type})\n'
        schema_text += "\n"
    
    prompt = f"""Bạn là chuyên gia SQL PostgreSQL. Hãy viết câu SQL trả lời câu hỏi tiếng Việt.

{schema_text}

QUY TẮC QUAN TRỌNG:
1. PHẢI bọc tất cả tên bảng và cột trong dấu ngoặc kép "" (vì PostgreSQL phân biệt chữ hoa/thường)
2. Tên bảng/cột phải CHÍNH XÁC như trong schema
3. Chỉ trả về MỘT câu SQL duy nhất, không giải thích
4. KHÔNG dùng markdown (```sql hoặc ```)
5. Với câu hỏi "ai có nhiều nhất":
   - Dùng COUNT, GROUP BY, ORDER BY ... DESC LIMIT 1
6. Với câu hỏi "ai ... và số lượng là bao nhiêu":
   - SELECT cả tên và COUNT trong cùng một câu
   - Dùng GROUP BY
7. Với câu hỏi đếm: COUNT(*)
8. Với câu hỏi liệt kê: SELECT * với LIMIT hợp lý

VÍ DỤ MẪU:
Hỏi: "Nhân sự nào có nhiều công việc nhất?"
→ SELECT "HoTen", COUNT(*) as "SoCongViec" FROM "NhanSu" JOIN "PhanCongNhanSu" ON "NhanSu"."ID" = "PhanCongNhanSu"."NhanSu_ID" GROUP BY "HoTen" ORDER BY COUNT(*) DESC LIMIT 1

Hỏi: "Có bao nhiêu dự án?"
→ SELECT COUNT(*) FROM "DuAn"

CÂU HỎI: {question}

Trả về ĐÚNG MỘT câu SQL (nhớ dùng dấu ngoặc kép):"""
    
    try:
        response = llm.invoke(prompt)
        
        # Xử lý response - có thể là object hoặc list
        if isinstance(response, list):
            sql = response[0].content.strip() if response else ""
        elif hasattr(response, 'content'):
            sql = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
        else:
            sql = str(response).strip()
        
        # Loại bỏ markdown nếu có
        if '```' in sql:
            # Tách ra các dòng
            lines = sql.split('\n')
            sql_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (line.strip() and not line.strip().startswith('#')):
                    sql_lines.append(line)
            sql = '\n'.join(sql_lines).strip()
        
        # Loại bỏ các dòng comment và chỉ giữ lại câu SQL
        if '\n' in sql:
            for line in sql.split('\n'):
                line = line.strip()
                if line and not line.startswith('--') and not line.startswith('#'):
                    if any(line.upper().startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
                        sql = line
                        break
        
        # Kiểm tra tính hợp lệ
        if not sql or 'ERROR' in sql.upper() or len(sql) < 10:
            return None
        
        return sql
    except Exception as e:
        print(f"⚠️ Lỗi Gemini: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 5. HÀM THỰC THI SQL TRỰC TIẾP
def run_sql_direct(sql_query):
    """Chạy SQL trực tiếp trên database và trả về DataFrame"""
    try:
        cursor.execute(sql_query)
        
        # Kiểm tra xem có kết quả trả về không
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            df = pd.DataFrame(results, columns=columns)
            return df
        else:
            conn.commit()
            return pd.DataFrame({"status": ["Query executed successfully"]})
    except Exception as e:
        conn.rollback()
        raise Exception(f"SQL Error: {str(e)}")

# 6. HỎI ĐÁP
print("\n" + "="*60)
print("💬 CHAT2DB - Hỏi đáp cơ sở dữ liệu PMIS (Powered by Gemini AI)")
print("="*60)
print("Bạn có thể:")
print("  1. Hỏi bằng tiếng Việt (AI sẽ tạo SQL)")
print("  2. Nhập SQL trực tiếp (bắt đầu bằng SELECT, INSERT, UPDATE, DELETE)")
print("  3. Gõ 'tables' để xem danh sách bảng")
print("  4. Gõ 'exit' để thoát")
print("="*60)

while True:
    question = input("\n❓ Câu hỏi của bạn: ").strip()
    
    if question.lower() == 'exit':
        print("👋 Tạm biệt!")
        break
    
    if question.lower() == 'tables':
        print(f"\n📋 Danh sách bảng ({len(tables)} bảng):")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        continue
    
    if not question:
        continue
    
    # Kiểm tra xem có phải SQL trực tiếp không
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'ALTER', 'DROP']
    is_direct_sql = any(question.upper().startswith(keyword) for keyword in sql_keywords)
    
    try:
        if is_direct_sql:
            # Chạy SQL trực tiếp
            print("⚙️ Đang thực thi SQL...")
            df = run_sql_direct(question)
            
            if not df.empty:
                print("\n✅ Kết quả:")
                print(df.to_string(index=False, max_rows=50, max_cols=20))
                print(f"\n📊 Tổng số dòng: {len(df)}")
            else:
                print("✅ Truy vấn thành công nhưng không có dữ liệu.")
        else:
            # Dùng Gemini AI để tạo SQL
            print("🤖 Gemini AI đang tạo SQL từ câu hỏi...")
            
            sql = generate_sql_with_gemini(question)
            
            if sql and isinstance(sql, str) and len(sql.strip()) > 0:
                print(f"\n📝 SQL được tạo:\n{sql}\n")
                
                # Chạy SQL
                print("⚙️ Đang thực thi...")
                df = run_sql_direct(sql)
                
                if not df.empty:
                    print("\n✅ Kết quả:")
                    print(df.to_string(index=False, max_rows=50, max_cols=20))
                    print(f"\n📊 Tổng số dòng: {len(df)}")
                else:
                    print("⚠️ Truy vấn không trả về dữ liệu.")
            else:
                print("⚠️ Gemini AI không thể tạo SQL. Hãy thử:")
                print("  - Diễn đạt lại câu hỏi rõ ràng hơn")
                print("  - Hoặc nhập SQL trực tiếp")
                
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        print("💡 Vui lòng kiểm tra lại câu hỏi hoặc SQL của bạn.")

# Đóng kết nối
cursor.close()
conn.close()
print("\n✅ Đã đóng kết nối database.")