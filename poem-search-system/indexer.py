import json
import logging
import re
import sys
import time

from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# --- CẤU HÌNH LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# --- CẤU HÌNH KẾT NỐI ---
# Dùng 127.0.0.1 để khớp với kết quả curl thành công của bạn
ES_HOST = "http://127.0.0.1:9200"
INDEX_NAME = "poems_hust_project"

# Tăng timeout lên 60s để tránh lỗi khi máy lag
es = Elasticsearch(ES_HOST, request_timeout=60)

# Load Model AI
# LƯU Ý: Lần chạy đầu tiên sẽ mất khoảng 5-10 phút để tải file 540MB.
# Vui lòng KHÔNG tắt ngang khi thấy thanh % đang chạy.
logging.info("⏳ Đang tải model AI (keepitreal/vietnamese-sbert)...")
model = SentenceTransformer('keepitreal/vietnamese-sbert')


def clean_poem_content(raw_text):
    """
    Hàm làm sạch dữ liệu:
    1. Loại bỏ các dòng chứa chữ Hán/Nôm.
    2. Loại bỏ các dòng trùng lặp.
    3. Giữ lại tiếng Việt sạch.
    """
    if not raw_text:
        return ""

    lines = raw_text.split('\n')
    clean_lines = []
    seen_lines = set()

    for line in lines:
        line = line.strip()
        
        # 1. Bỏ dòng rỗng hoặc quá ngắn
        if not line or len(line) < 2:
            continue
            
        # 2. Bỏ dòng chứa ký tự Hán/Nôm (Unicode range \u4e00-\u9fff)
        if re.search('[\u4e00-\u9fff]', line):
            continue
            
        # 3. Bỏ dòng trùng lặp (check không phân biệt hoa thường)
        line_lower = line.lower()
        if line_lower in seen_lines:
            continue
        
        seen_lines.add(line_lower)
        clean_lines.append(line)
    
    # Ghép lại thành đoạn văn
    return "\n".join(clean_lines)


def create_index():
    """Tạo Index và Mapping trong Elasticsearch"""
    
    # --- FIX QUAN TRỌNG: Dùng info() thay vì ping() để tránh lỗi 400 ---
    try:
        server_info = es.info()
        logging.info(f"🔗 Kết nối thành công tới Elasticsearch v{server_info['version']['number']}")
    except Exception as e:
        logging.error(f"❌ Không thể kết nối đến {ES_HOST}. Lỗi chi tiết: {e}")
        logging.error("👉 Hãy kiểm tra: docker ps (xem container chạy chưa)")
        sys.exit(1)

    # Xóa index cũ nếu tồn tại (ignore lỗi 400/404)
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
        logging.info(f"🗑️ Đã xóa index cũ: {INDEX_NAME}")
    
    # Định nghĩa cấu trúc dữ liệu
    settings = {
        "mappings": {
            "properties": {
                # --- Field cho Full-text Search (BM25) ---
                "poem_title": {"type": "text", "analyzer": "standard"},
                "author": {"type": "keyword"},
                "poem_content_text": {"type": "text", "analyzer": "standard"},
                "the_tho": {"type": "keyword"},
                "thoi_ky": {"type": "keyword"},
                
                # --- Field cho Vector Search (Semantic) ---
                "poem_vector": {
                    "type": "dense_vector",
                    "dims": 768,           # Kích thước vector của model sbert
                    "index": True,
                    "similarity": "cosine" # Dùng cosine similarity để so sánh ý nghĩa
                }
            }
        }
    }
    
    es.indices.create(index=INDEX_NAME, body=settings)
    logging.info(f"✅ Đã tạo mới Index: {INDEX_NAME}")


def generate_docs():
    """Đọc file JSON, làm sạch và vector hóa"""
    try:
        with open('poems.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error("❌ Không tìm thấy file 'poems.json'. Hãy chắc chắn file data đang ở cùng thư mục.")
        sys.exit(1)
    
    logging.info(f"🚀 Bắt đầu xử lý {len(data)} bài thơ đầu vào...")
    
    count_valid = 0
    count_skipped = 0
    
    for poem in data:
        # 1. Làm sạch nội dung
        raw_content = poem.get('poem_content_text', '')
        cleaned_content = clean_poem_content(raw_content)
        
        # Nếu sau khi lọc mà nội dung quá ngắn (< 20 ký tự) thì bỏ qua
        if len(cleaned_content) < 20:
            count_skipped += 1
            continue

        # 2. Tạo Vector (Embedding)
        # Kết hợp Title + Content để AI hiểu ngữ cảnh đầy đủ
        text_to_vector = f"{poem['poem_title']} {cleaned_content}"
        
        # Encode (Cắt ngắn text xuống 512 từ để tránh quá tải model)
        vector = model.encode(text_to_vector[:1000]).tolist()
        
        count_valid += 1
        
        # 3. Trả về document chuẩn ES
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "poem_title": poem['poem_title'],
                "author": poem['author'],
                "poem_content_text": cleaned_content, # Lưu bản sạch
                "the_tho": poem.get('the_tho', ''),
                "thoi_ky": poem.get('thoi_ky', ''),
                "url": poem.get('url', ''),
                "poem_vector": vector
            }
        }
    
    logging.info(f"⚠️ Đã bỏ qua {count_skipped} bài (rác/Hán/Nôm).")
    logging.info(f"📦 Đang đẩy {count_valid} bài thơ sạch vào Elasticsearch...")


def main():
    create_index()
    # Bulk index (đẩy hàng loạt) để tối ưu tốc độ
    try:
        start_time = time.time()
        success, failed = helpers.bulk(es, generate_docs(), stats_only=True)
        duration = time.time() - start_time
        logging.info(f"🎉 HOÀN TẤT! Đã index {success} bài thơ trong {duration:.2f}s.")
        if failed > 0:
            logging.warning(f"⚠️ Có {failed} bài bị lỗi khi index.")
    except Exception as e:
        logging.error(f"❌ Lỗi trong quá trình Bulk Index: {e}")

if __name__ == "__main__":
    main()