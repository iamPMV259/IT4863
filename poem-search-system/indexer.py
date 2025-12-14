import json
import logging

from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# Setup Log cho dễ nhìn
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# 1. Kết nối Elasticsearch
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "poems_hust_project"

# 2. Load Model AI (Vietnamese SBERT)
# Model này sẽ biến văn bản thành vector 768 chiều
logging.info("⏳ Đang tải model AI (lần đầu sẽ hơi lâu)...")
model = SentenceTransformer('keepitreal/vietnamese-sbert')

def create_index():
    """Tạo cấu trúc bảng (Index Mapping)"""
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    
    settings = {
        "mappings": {
            "properties": {
                # --- Nhóm field cho BM25 & Hiển thị ---
                "poem_title": {"type": "text", "analyzer": "standard"},
                "author": {"type": "keyword"}, # Keyword để filter chính xác
                "poem_content_text": {"type": "text", "analyzer": "standard"},
                "the_tho": {"type": "keyword"},
                "thoi_ky": {"type": "keyword"},
                "url": {"type": "keyword"},
                
                # --- Nhóm field cho Semantic Search (Chương 4) ---
                "poem_vector": {
                    "type": "dense_vector",
                    "dims": 768, # Kích thước vector của model sbert
                    "index": True,
                    "similarity": "cosine" # Dùng cosine similarity để đo khoảng cách
                }
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=settings)
    logging.info(f"✅ Đã tạo Index: {INDEX_NAME}")

def generate_docs():
    """Đọc JSON và tạo generator để đẩy vào ES"""
    with open('poems.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logging.info(f"🚀 Bắt đầu xử lý {len(data)} bài thơ...")
    
    for poem in data:
        # Kết hợp Tiêu đề + Nội dung để AI hiểu ngữ cảnh tốt hơn
        combined_text = f"{poem['poem_title']} {poem['poem_content_text']}"
        
        # Tạo Vector (Embedding)
        vector = model.encode(combined_text).tolist()
        
        # Tạo document để đẩy lên ES
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "poem_title": poem['poem_title'],
                "author": poem['author'],
                "poem_content_text": poem['poem_content_text'],
                "the_tho": poem.get('the_tho', ''),
                "thoi_ky": poem.get('thoi_ky', ''),
                "url": poem.get('url', ''),
                "poem_vector": vector # Vector nằm ở đây
            }
        }

def main():
    create_index()
    # Sử dụng bulk helper để đẩy dữ liệu nhanh hơn
    success, _ = helpers.bulk(es, generate_docs())
    logging.info(f"🎉 Hoàn tất! Đã index thành công {success} bài thơ.")

if __name__ == "__main__":
    main()