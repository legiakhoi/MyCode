import os
import warnings
warnings.filterwarnings("ignore", message="Core Pydantic V1")

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 1. Cấu hình Gemini
GEMINI_API_KEY = "AIzaSyDiXw9ZierqpR3rxFU1aHgxeuLZFVrAkco"
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=GEMINI_API_KEY)

# 2. Giả lập dữ liệu: Một đoạn trong Luật Đất đai và một đoạn trong Nghị định hướng dẫn
law_text = "Điều 10. Phân loại đất. Căn cứ vào mục đích sử dụng, đất đai được phân loại..."
decree_text = "Điều 3. Xác định loại đất. Việc xác định loại đất quy định tại Điều 10 Luật Đất đai thực hiện như sau..."

# 3. Chunking & Indexing (Lưu vào Vector DB)
# Trong thực tế, bạn sẽ dùng Regex để tách theo "Điều"
docs = [
    Document(page_content=law_text, metadata={"source": "Luật Đất đai 2024", "article": "Điều 10"}),
    Document(page_content=decree_text, metadata={"source": "Nghị định 102/2024/NĐ-CP", "article": "Điều 3"})
]

vector_db = FAISS.from_documents(docs, embeddings)

# 4. Hàm tìm kiếm thông tin liên quan (Contextual Lookup)
def get_related_legal_info(current_text_reading):
    # Tìm kiếm các đoạn văn bản có ý nghĩa tương đồng (Semantic Search)
    results = vector_db.similarity_search(current_text_reading, k=2)
    
    context_str = ""
    for doc in results:
        # Loại bỏ chính văn bản đang đọc để tránh trùng lặp
        if doc.page_content != current_text_reading:
            context_str += f"- Trích {doc.metadata['source']} ({doc.metadata['article']}): {doc.page_content}\n"
    
    return context_str

# 5. Hàm AI phân tích mối liên hệ
def analyze_connection(current_text, related_context):
    if not related_context:
        return "Không tìm thấy văn bản liên quan trực tiếp."
        
    prompt = f"""
    Tôi đang đọc văn bản này: "{current_text}"
    
    Hệ thống tìm thấy các quy định liên quan sau:
    {related_context}
    
    Hãy đóng vai trò chuyên gia luật, phân tích ngắn gọn: Các văn bản liên quan trên bổ sung, hướng dẫn hay giới hạn điều gì đối với văn bản tôi đang đọc?
    """
    response = llm.invoke(prompt)
    # Xử lý response - có thể là string hoặc list
    content = response.content
    if isinstance(content, list):
        # Nếu là list, lấy text từ phần tử đầu tiên
        return content[0].get('text', str(content)) if content else ""
    return content

# --- CHẠY THỬ ---
user_reading = decree_text # Giả sử user đang đọc Nghị định
related_info = get_related_legal_info(user_reading)
ai_analysis = analyze_connection(user_reading, related_info)

print("--- ĐANG ĐỌC ---")
print(user_reading)
print("\n--- AI GỢI Ý LIÊN KẾT ---")
print(ai_analysis)