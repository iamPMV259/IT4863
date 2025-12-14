import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# --- CẤU HÌNH ---
st.set_page_config(page_title="HUST Poem Search", layout="wide")

# Kết nối ES (Dùng 127.0.0.1 như bên indexer)
es = Elasticsearch("http://127.0.0.1:9200", request_timeout=30)
INDEX_NAME = "poems_hust_project"

@st.cache_resource
def load_model():
    return SentenceTransformer('keepitreal/vietnamese-sbert')

model = load_model()

# --- HEADER & SIDEBAR ---
st.title("🔎 Hệ thống Tìm kiếm Thơ (Hybrid Search)")
st.caption(f"Trạng thái kết nối ES: {'🟢 Online' if es.ping() else '🔴 Offline'}")

with st.sidebar:
    st.header("⚙️ Cấu hình Tìm kiếm")
    search_mode = st.radio(
        "Chọn thuật toán:",
        ("Mô hình Xác suất (BM25)", "Mô hình Vector (Semantic)")
    )
    
    st.divider()
    st.info("""
    **Giải thích:**
    1. **BM25 (Best Matching):** Tìm dựa trên từ khóa chính xác và tần suất xuất hiện.
    2. **Semantic Search:** Tìm dựa trên ý nghĩa, ngữ cảnh vector (AI).
    """)

# --- MAIN UI ---
query = st.text_input("Nhập từ khóa, câu thơ hoặc tâm trạng:", placeholder="Ví dụ: Nỗi nhớ mùa thu...")

if st.button("Tìm kiếm", type="primary") or query:
    if not query.strip():
        st.warning("Vui lòng nhập nội dung tìm kiếm!")
    else:
        results = []
        try:
            if search_mode == "Mô hình Xác suất (BM25)":
                # --- LOGIC BM25 ---
                body = {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["poem_title^3", "poem_content_text"], # Title quan trọng x3
                            "fuzziness": "AUTO" # Chấp nhận sai chính tả nhẹ
                        }
                    },
                    "size": 5
                }
                resp = es.search(index=INDEX_NAME, body=body)
                results = resp['hits']['hits']
                
            else:
                # --- LOGIC VECTOR ---
                query_vector = model.encode(query).tolist()
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

            # --- HIỂN THỊ KẾT QUẢ ---
            st.subheader(f"Kết quả ({len(results)} bài phù hợp):")
            
            if not results:
                st.info("Không tìm thấy bài thơ nào. Thử từ khóa khác xem sao!")
            
            for hit in results:
                score = hit['_score']
                src = hit['_source']
                
                with st.expander(f"📖 {src['poem_title']} - {src['author']} (Score: {score:.2f})", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Hiển thị nội dung (cắt 6 dòng đầu)
                        content_lines = src['poem_content_text'].split('\n')
                        preview = "\n".join(content_lines[:6])
                        st.text(preview + ("\n..." if len(content_lines) > 6 else ""))
                    
                    with col2:
                        st.badge(src.get('the_tho', 'N/A'))
                        st.caption(f"Thời kỳ: {src.get('thoi_ky', 'N/A')}")
                        st.caption(f"ID: {hit['_id']}")
                        
        except Exception as e:
            st.error(f"Lỗi khi tìm kiếm: {e}")