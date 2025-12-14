import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# --- Cấu hình ---
st.set_page_config(page_title="HUST Poem Search", layout="wide")
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "poems_hust_project"

# Cache model để app chạy nhanh, không load lại model mỗi lần bấm nút
@st.cache_resource
def load_model():
    return SentenceTransformer('keepitreal/vietnamese-sbert')

model = load_model()

# --- Giao diện ---
st.title("🔎 Hệ thống Tìm kiếm Thơ (Hybrid Search)")
st.caption("Demo môn học: So sánh BM25 (Xác suất) và Vector Space (Ngữ nghĩa)")

with st.sidebar:
    st.header("⚙️ Cấu hình")
    search_mode = st.radio(
        "Chọn thuật toán:",
        ("Mô hình Xác suất (BM25)", "Mô hình Vector (Semantic)")
    )
    st.info("""
    **Giải thích:**
    - **BM25:** Tìm từ khóa chính xác (dựa trên tần suất).
    - **Vector:** Tìm theo ý nghĩa/ngữ cảnh (dựa trên AI).
    """)

query = st.text_input("Nhập từ khóa hoặc tâm trạng (VD: 'Nỗi nhớ mùa thu')", "")

# --- Xử lý Tìm kiếm ---
if st.button("Tìm kiếm") or query:
    results = []
    
    if search_mode == "Mô hình Xác suất (BM25)":
        # === PHƯƠNG PHÁP 1: BM25 ===
        # Tìm chính xác từ khóa trong Title và Content
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["poem_title^3", "poem_content_text"], # Title quan trọng gấp 3
                    "type": "best_fields"
                }
            },
            "size": 5
        }
        resp = es.search(index=INDEX_NAME, body=body)
        results = resp['hits']['hits']
        
    else:
        # === PHƯƠNG PHÁP 2: VECTOR SEARCH ===
        # 1. Biến query của user thành vector
        query_vector = model.encode(query).tolist()
        
        # 2. Tìm vector gần nhất (KNN)
        body = {
            "knn": {
                "field": "poem_vector",
                "query_vector": query_vector,
                "k": 5,
                "num_candidates": 100
            },
            "_source": ["poem_title", "author", "poem_content_text", "the_tho", "thoi_ky"] 
        }
        resp = es.search(index=INDEX_NAME, body=body)
        results = resp['hits']['hits']

    # --- Hiển thị Kết quả ---
    st.subheader(f"Kết quả cho: '{query}'")
    
    if not results:
        st.warning("Không tìm thấy bài thơ nào phù hợp.")
    
    for hit in results:
        score = hit['_score']
        source = hit['_source']
        
        # Card hiển thị từng bài thơ
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.metric(label="Độ phù hợp (Score)", value=f"{score:.2f}")
                st.badge(source.get('the_tho', 'Unknown'))
            
            with col2:
                st.markdown(f"### 📖 {source['poem_title']}")
                st.text(f"Tác giả: {source['author']} | Thời kỳ: {source.get('thoi_ky', 'N/A')}")
                
                # Hiển thị trích đoạn (4 dòng đầu)
                content = source['poem_content_text']
                preview = "\n".join(content.split('\n')[:4])
                st.code(preview + "\n...", language="text")
                
                with st.expander("Xem toàn bộ bài thơ"):
                    st.write(content)
            st.divider()