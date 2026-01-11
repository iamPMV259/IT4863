# app.py
import html
import math
import unicodedata

import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

ES_HOST = "http://localhost:9200"
INDEX_NAME = "vietnamese_poems"
PAGE_SIZE = 25

es = Elasticsearch(ES_HOST)
model = SentenceTransformer("intfloat/multilingual-e5-small")

st.set_page_config(
    page_title="Tìm kiếm thơ tiếng Việt",
    layout="wide"
)

def remove_accent(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def render_poem(text: str) -> str:
    return html.escape(text)


def build_query(query_text, page, alpha, beta):

    query_vector = model.encode(
        f"query: {query_text}",
        normalize_embeddings=True
    ).tolist()

    from_ = (page - 1) * PAGE_SIZE

    return {
        "from": from_,
        "size": PAGE_SIZE,
        "query": {
            "script_score": {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query_text,
                                    "fields": [
                                        "ten_bai^3",
                                        "noi_dung_tho^2",
                                        "tac_gia"
                                    ]
                                }
                            },
                            {
                                "multi_match": {
                                    "query": remove_accent(query_text),
                                    "fields": [
                                        "noi_dung_tho_khong_dau"
                                    ]
                                }
                            }
                        ]
                    }
                },
                "script": {
                    "source": """
                        double bm25 = _score;
                        double cosine = cosineSimilarity(params.query_vector, 'embedding');
                        return params.alpha * bm25 + params.beta * cosine;
                    """,
                    "params": {
                        "query_vector": query_vector,
                        "alpha": alpha,
                        "beta": beta
                    }
                }
            }
        }
    }


st.title("Hệ thống tìm kiếm thơ tiếng Việt")

query = st.text_input(
    "Nhập câu thơ, chủ đề hoặc cảm xúc:",
    placeholder="Ví dụ: nỗi nhớ quê, chiều thu, ly biệt..."
)

with st.sidebar:
    st.header("Tuỳ chỉnh xếp hạng")
    alpha = st.slider("Trọng số BM25", 0.0, 1.0, 0.6, 0.05)
    beta = st.slider("Trọng số Vector similarity", 0.0, 1.0, 0.4, 0.05)

    st.markdown("---")
    page = st.number_input(
        "Trang",
        min_value=1,
        value=1,
        step=1
    )

if query:
    body = build_query(query, page, alpha, beta)
    res = es.search(index=INDEX_NAME, body=body)

    hits = res["hits"]["hits"]
    total = res["hits"]["total"]["value"]
    total_pages = math.ceil(total / PAGE_SIZE)

    st.subheader(f"Tìm thấy {total} bài thơ")

    for hit in hits:
        src = hit["_source"]
        score = hit["_score"]

        st.markdown("---")
        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown(f"### {src.get('ten_bai', '')}")
            poem_text = render_poem(src.get("noi_dung_tho", ""))

            st.caption(f"Độ phù hợp: {score:.4f}")
            st.text_area("Nội dung", poem_text, height=200, key=hit['_id'])



        with col_right:
            st.markdown("**Thông tin bài thơ**")
            st.markdown(f"**Tác giả:** {src.get('tac_gia', '—')}")
            st.markdown(f"**Thời kỳ:** {src.get('thoi_ky', '—')}")
            st.markdown(f"**Thể thơ:** {src.get('the_tho', '—')}")
            st.markdown(f"**Tập thơ:** {src.get('tap_tho', '—')}")
            st.markdown(
                f"[Xem nguồn]({src.get('url', '#')})"
            )

    st.markdown("---")
    st.markdown(
        f"Trang **{page} / {total_pages}** — mỗi trang {PAGE_SIZE} kết quả"
    )

else:
    st.info("Hãy nhập truy vấn để bắt đầu tìm kiếm thơ.")
