
import json
import unicodedata

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

ES_HOST = "http://localhost:9200"
INDEX_NAME = "vietnamese_poems"
DATA_FILE = "poem_full_data.json"


def remove_accent(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


es = Elasticsearch(ES_HOST)


model = SentenceTransformer("intfloat/multilingual-e5-small")


def create_index():
    if es.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "vi_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "ten_bai": {
                    "type": "text",
                    "analyzer": "vi_analyzer"
                },
                "tac_gia": {
                    "type": "text",
                    "analyzer": "vi_analyzer"
                },
                "tap_tho": {"type": "keyword"},
                "thoi_ky": {"type": "keyword"},
                "the_tho": {"type": "keyword"},
                "noi_dung_tho": {
                    "type": "text",
                    "analyzer": "vi_analyzer"
                },
                "noi_dung_tho_khong_dau": {
                    "type": "text",
                    "analyzer": "vi_analyzer"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=mapping)

def index_poems():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        poems = json.load(f)


    for poem in tqdm(poems):
        content = poem.get("noi_dung_tho", "")

        embedding = model.encode(
            f"passage: {content}",
            normalize_embeddings=True
        ).tolist()

        doc = {
            "url": poem.get("url"),
            "ten_bai": poem.get("ten_bai"),
            "tac_gia": poem.get("tac_gia"),
            "tap_tho": poem.get("tap_tho"),
            "thoi_ky": poem.get("thoi_ky"),
            "the_tho": poem.get("the_tho"),
            "noi_dung_tho": content,
            "noi_dung_tho_khong_dau": remove_accent(content),
            "embedding": embedding
        }

        es.index(index=INDEX_NAME, document=doc)

    es.indices.refresh(index=INDEX_NAME)

if __name__ == "__main__":
    create_index()
    index_poems()
