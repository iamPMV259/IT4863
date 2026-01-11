import json
import os


def load_data():
    poem_metadata = json.load(open("poem_metadata.json", "r", encoding="utf-8"))

    print(f"Loaded {len(poem_metadata)} poems' metadata.")


    crawled_poems = json.load(open("poem_full_data_1.json", "r", encoding="utf-8"))
    
    print(f"Loaded {len(crawled_poems)} crawled poems' full data.")

    poem_urls = json.load(open("poem_urls_part_1.json", "r", encoding="utf-8"))
    poem_urls_dict = {item['url']: item for item in poem_urls}

    print(f"Loaded {len(poem_urls)} poem URLs.")

    for item in crawled_poems:
        if item['url'].find("robot-check.php") != -1:
            continue
        poem_urls_dict.pop(item['url'], None)
        if not item.get('ten_bai'):
            continue
        poem_metadata.append(item)

    print(f"After merging, we have {len(poem_metadata)} poems' metadata.")

    poem_urls_remaining = list(poem_urls_dict.values())
    print(f"Remaining {len(poem_urls_remaining)} poem URLs to crawl.")

    json.dump(poem_metadata, open("poem_metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(poem_urls_remaining, open("poem_urls_part_1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            


if __name__ == "__main__":
    load_data()