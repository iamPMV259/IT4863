import math

import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="HUST Poem Search v3", layout="wide")

try:
    es = Elasticsearch("http://127.0.0.1:9200", request_timeout=30)
    info = es.info()
    es_status = f"Online (v{info['version']['number']})"
except Exception:
    es_status = "Offline"

INDEX_NAME = "poems_hust_project"
PAGE_SIZE = 10

@st.cache_resource
def load_model():
    return SentenceTransformer('keepitreal/vietnamese-sbert')

model = load_model()


SYNONYMS = {
    "trăng": ["nguyệt", "hằng", "chị hằng", "cung quế"],
    "nguyệt": ["trăng"],
    "rượu": ["tửu", "men"],
    "tửu": ["rượu"],
    "xuân": ["tết"],
    "thu": ["heo may"],
    "nhớ": ["tương tư", "hoài mong"]
}

def expand_query(user_query):
    tokens = user_query.lower().split()
    expanded_terms = []
    for token in tokens:
        if token in SYNONYMS:
            expanded_terms.extend(SYNONYMS[token])
    return " ".join(expanded_terms)


st.markdown("""
<style>
    .poem-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2ecc71; }
    .poem-title { color: #2c3e50; font-size: 1.15rem; font-weight: bold; }
    .poem-meta { font-size: 0.85rem; color: #7f8c8d; margin-bottom: 8px; }
    .highlight-match { background-color: #fff3cd; padding: 0 2px; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Cấu hình")
    st.caption(f"Status: {es_status}")
    search_mode = st.radio("Chế độ:", ("Hybrid (Thông minh)", "BM25 (Từ khóa)", "Semantic (Vector)"), index=0)


if 'page' not in st.session_state:
    st.session_state.page = 1
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""


st.title("HUST Poem Search Engine")


query = st.text_input("Nhập từ khóa:", placeholder="VD: Trăng, rượu, nỗi nhớ...", key="search_input")


if query != st.session_state.last_query:
    st.session_state.page = 1
    st.session_state.last_query = query

if query:
    
    synonym_text = expand_query(query)
    
    
    es_from = (st.session_state.page - 1) * PAGE_SIZE
    
    
    text_query = {
        "bool": {
            "should": [
                
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["poem_title^5", "poem_content_text^3"],
                        "type": "phrase",
                        "boost": 10 
                        
                    }
                },
                
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["poem_title^3", "poem_content_text"],
                        "operator": "and",
                        "boost": 5
                    }
                },
                
                {
                    "multi_match": {
                        "query": synonym_text,
                        "fields": ["poem_title", "poem_content_text"],
                        "boost": 3
                    }
                },
                
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["poem_title", "poem_content_text"],
                        "fuzziness": "AUTO",
                        "boost": 0.5 
                        
                    }
                }
            ]
        }
    }
    
    vector_embedding = model.encode(query).tolist()
    knn_query = {
        "field": "poem_vector",
        "query_vector": vector_embedding,
        "k": 50,
        "num_candidates": 200,
        "boost": 1.0
    }

    search_body = {
        "from": es_from,
        "size": PAGE_SIZE,
        "_source": ["poem_title", "author", "the_tho", "thoi_ky", "poem_content_text"],

        "track_total_hits": True 
    }

    if search_mode == "BM25 (Từ khóa)":
        search_body["query"] = text_query
    elif search_mode == "Semantic (Vector)":
        search_body["knn"] = knn_query
    else: 
        search_body["query"] = text_query
        search_body["knn"] = knn_query

    try:
        resp = es.search(index=INDEX_NAME, body=search_body)
        hits = resp['hits']['hits']
        total_hits = resp['hits']['total']['value']
        total_pages = math.ceil(total_hits / PAGE_SIZE)

        st.caption(f"Tìm thấy tổng cộng **{total_hits}** bài thơ (Trang {st.session_state.page}/{total_pages})")
        
        if total_hits == 0:
            st.warning("Không tìm thấy kết quả nào.")
        else:
            for i, hit in enumerate(hits):
                src = hit['_source']
                content = src.get('poem_content_text', '')
                preview = "\n".join(content.split('\n')[:6])
                
                with st.container():
                    st.markdown(f"""
                    <div class="poem-card">
                        <div class="poem-title">{es_from + i + 1}. {src.get('poem_title')}</div>
                        <div class="poem-meta">
                             {src.get('author')} | 🎼 {src.get('the_tho')} | Score: {hit['_score']:.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Xem nội dung"):
                        st.text(content)

            st.divider()
            c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
            
            with c2:
                if st.session_state.page > 1:
                    if st.button("Trang trước"):
                        st.session_state.page -= 1
                        st.rerun()
            
            with c3:
                if st.session_state.page < total_pages:
                    if st.button("Trang sau"):
                        st.session_state.page += 1
                        st.rerun()

    except Exception as e:
        st.error(f"Lỗi truy vấn: {e}")
