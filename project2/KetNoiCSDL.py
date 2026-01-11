import os
import asyncio
from dotenv import load_dotenv # Import thư viện
from vanna.integrations.google.gemini import GeminiLlmService
from vanna.legacy.chromadb import ChromaDB_VectorStore
from vanna.core.llm import LlmRequest, LlmMessage
from vanna.core import User

# 1. Load các biến từ file .env vào môi trường
load_dotenv()

# 2. Lấy API Key và DB Config từ môi trường
api_key = os.getenv("GEMINI_API_KEY")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD") # Đã sửa thành DB_PASSWORD cho đúng với .env

# Kiểm tra xem đã lấy được key chưa (để debug)
if not api_key:
    raise ValueError("Chưa tìm thấy GEMINI_API_KEY trong file .env")

# 3. Cấu hình Vanna với ChromaDB (Local) và Gemini (Modern)
class MyVanna(ChromaDB_VectorStore, GeminiLlmService):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        GeminiLlmService.__init__(self, api_key=config['api_key'], model=config['model'])

    # Implement Legacy methods required by ChromaDB_VectorStore (via VannaBase)
    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, messages: list, **kwargs) -> str:
        # Map legacy messages to LlmRequest
        llm_messages = []
        system_prompt = None
        
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                llm_messages.append(LlmMessage(role='user', content=msg['content']))
            elif msg['role'] == 'assistant':
                llm_messages.append(LlmMessage(role='assistant', content=msg['content']))
        
        if not llm_messages:
            raise ValueError("No messages found in the prompt")
        
        # Create User object (required by LlmRequest)
        user = User(id="default", username="default_user", email="default@example.com")
        
        # Create LlmRequest with the correct structure
        request = LlmRequest(
            messages=llm_messages,
            user=user,
            system_prompt=system_prompt,
            temperature=kwargs.get('temperature', 0.7)
        )
        
        # Run async method synchronously
        try:
            response = asyncio.run(self.send_request(request))
            if response is None:
                raise ValueError("LLM returned None response")
            if hasattr(response, 'content') and response.content:
                return response.content
            else:
                raise ValueError(f"LLM response has no content: {response}")
        except RuntimeError:
            # Handle case where loop is already running
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new loop for this thread
                    import nest_asyncio
                    nest_asyncio.apply()
                    response = asyncio.run(self.send_request(request))
                else:
                    response = loop.run_until_complete(self.send_request(request))
                if response is None:
                    raise ValueError("LLM returned None response")
                if hasattr(response, 'content') and response.content:
                    return response.content
                else:
                    raise ValueError(f"LLM response has no content: {response}")
            except Exception as e2:
                raise
        except Exception as e:
            raise

# Khởi tạo Vanna với path lưu vector db cục bộ
vn = MyVanna(config={
    'api_key': api_key, 
    'model': 'gemini-1.5-flash',
    'path': './chroma_db_data' # Thư mục lưu dữ liệu training
})

print("Đang kết nối đến PostgreSQL...")
try:
    vn.connect_to_postgres(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_pass,
        port=2345
    )
    # Test connection
    vn.run_sql("SELECT 1")
    print("---> Kết nối CSDL thành công!")
except Exception as e:
    print(f"---> Lỗi kết nối CSDL: {e}")
    exit(1)

# 4. Huấn luyện bot với dữ liệu từ CSDL (Tự động lấy Schema)
print("\nĐang quét schema database để huấn luyện...")
try:
    # Lấy danh sách bảng
    df_tables = vn.run_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    
    if df_tables is not None and not df_tables.empty:
        for index, row in df_tables.iterrows():
            table_name = row['table_name']
            # Lấy thông tin cột
            df_columns = vn.run_sql(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
            
            if df_columns is not None and not df_columns.empty:
                # Tạo câu lệnh DDL giả lập để train
                ddl_parts = [f"{r['column_name']} {r['data_type']}" for _, r in df_columns.iterrows()]
                ddl = f"CREATE TABLE {table_name} ({', '.join(ddl_parts)});"
                
                # Train Vanna
                vn.train(ddl=ddl)
                print(f"   + Đã train bảng: {table_name}")
    else:
        print("   ! Không tìm thấy bảng nào trong schema 'public'.")

except Exception as e:
    print(f"Lỗi khi huấn luyện: {e}")

print("------------------------------------------------------")
print("Bot SQL đã sẵn sàng! Gõ 'exit' để thoát chương trình.")
print("------------------------------------------------------")

# Tự động test một câu hỏi
test_question = "Liệt kê các bảng trong cơ sở dữ liệu?"
print(f"\n[AUTO-TEST] Câu hỏi: {test_question}")
try:
    sql, df, fig = vn.ask(question=test_question, print_results=False)
    print(f"---> SQL sinh ra: {sql}")
    print(f"---> Kết quả:\n{df}")
except Exception as e:
    print(f"[AUTO-TEST] Lỗi: {e}")
    if "API key" in str(e).lower() or "INVALID_ARGUMENT" in str(e):
        print("\n[!] LỖI: API Key Gemini đã hết hạn hoặc không hợp lệ.")
        print("[!] Vui lòng kiểm tra lại GEMINI_API_KEY trong file .env")

while True:
    # 1. Cho phép người dùng nhập câu hỏi
    user_question = input("\nBạn muốn hỏi gì về dữ liệu? (Mời nhập): ")

    # 2. Kiểm tra điều kiện thoát
    if user_question.lower() in ['exit', 'thoat', 'quit']:
        print("Tạm biệt!")
        break
    
    if not user_question.strip():
        continue

    # 3. Gửi câu hỏi cho Gemini
    try:
        sql, df, fig = vn.ask(question=user_question, print_results=False)

        # 4. Hiển thị kết quả ra màn hình đen
        print(f"\n---> SQL sinh ra: {sql}")
        print("\n---> Kết quả tìm được:")
        print(df) # In bảng dữ liệu (DataFrame)
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        if "API key" in str(e).lower() or "INVALID_ARGUMENT" in str(e):
            print("\n[!] LỖI: API Key Gemini đã hết hạn hoặc không hợp lệ.")
            print("[!] Vui lòng kiểm tra lại GEMINI_API_KEY trong file .env")
