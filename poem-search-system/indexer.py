import json
import logging
import re
import sys
import time

from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

ES_HOST = "http://127.0.0.1:9200"
INDEX_NAME = "poems_hust_project"

es = Elasticsearch(ES_HOST, request_timeout=60)

logging.info("Đang tải model AI (keepitreal/vietnamese-sbert)...")
model = SentenceTransformer('keepitreal/vietnamese-sbert')


def clean_poem_content(raw_text):
    if not raw_text:
        return ""

    lines = raw_text.split('\n')
    clean_lines = []
    seen_lines = set()

    for line in lines:
        line = line.strip()
        
        if not line or len(line) < 2:
            continue
            
        if re.search('[\u4e00-\u9fff]', line):
            continue
            
        line_lower = line.lower()
        if line_lower in seen_lines:
            continue
        
        seen_lines.add(line_lower)
        clean_lines.append(line)
    
    return "\n".join(clean_lines)


def create_index():
    try:
        server_info = es.info()
        logging.info(f"Kết nối thành công tới Elasticsearch v{server_info['version']['number']}")
    except Exception as e:
        logging.error(f"Không thể kết nối đến {ES_HOST}. Lỗi chi tiết: {e}")
        logging.error("Hãy kiểm tra: docker ps")
        sys.exit(1)

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
        logging.info(f"Đã xóa index cũ: {INDEX_NAME}")
    
    settings = {
        "mappings": {
            "properties": {
                "poem_title": {"type": "text", "analyzer": "standard"},
                "author": {"type": "keyword"},
                "poem_content_text": {"type": "text", "analyzer": "standard"},
                "the_tho": {"type": "keyword"},
                "thoi_ky": {"type": "keyword"},
                
                "poem_vector": {
                    "type": "dense_vector",
                    "dims": 768,          
                    "index": True,
                    "similarity": "cosine" 
                }
            }
        }
    }
    
    es.indices.create(index=INDEX_NAME, body=settings)
    logging.info(f"Đã tạo mới Index: {INDEX_NAME}")


def generate_docs():
    try:
        with open('poems.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error("Không tìm thấy file 'poems.json'. Hãy chắc chắn file data đang ở cùng thư mục.")
        sys.exit(1)
    
    logging.info(f"Bắt đầu xử lý {len(data)} bài thơ đầu vào...")
    
    count_valid = 0
    count_skipped = 0
    
    for poem in data:
        raw_content = poem.get('poem_content_text', '')
        cleaned_content = clean_poem_content(raw_content)
        
        if len(cleaned_content) < 20:
            count_skipped += 1
            continue

        text_to_vector = f"{poem['poem_title']} {cleaned_content}"
        
        vector = model.encode(text_to_vector[:1000]).tolist()
        
        count_valid += 1
        
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "poem_title": poem['poem_title'],
                "author": poem['author'],
                "poem_content_text": cleaned_content,
                "the_tho": poem.get('the_tho', ''),
                "thoi_ky": poem.get('thoi_ky', ''),
                "url": poem.get('url', ''),
                "poem_vector": vector
            }
        }
    
    logging.info(f"Đã bỏ qua {count_skipped} bài (rác/Hán/Nôm).")
    logging.info(f"Đang đẩy {count_valid} bài thơ sạch vào Elasticsearch...")


def main():
    create_index()
    try:
        start_time = time.time()
        success, failed = helpers.bulk(es, generate_docs(), stats_only=True)
        duration = time.time() - start_time
        logging.info(f"HOÀN TẤT! Đã index {success} bài thơ trong {duration:.2f}s.")
        if failed > 0:
            logging.warning(f"Có {failed} bài bị lỗi khi index.")
    except Exception as e:
        logging.error(f"Lỗi trong quá trình Bulk Index: {e}")

if __name__ == "__main__":
    main()