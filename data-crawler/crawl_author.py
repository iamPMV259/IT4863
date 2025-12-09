import json

import scrapy
from scrapy.crawler import CrawlerProcess


class ThivienAuthorSpider(scrapy.Spider):
    name = "thivien_author"
    
    authors_list = json.load(open('authors_list.json', 'r', encoding='utf8'))
    # URL tác giả bạn cung cấp
    start_urls = [author['url'] for author in authors_list]
    start_urls = list(set(start_urls))  # Loại bỏ trùng lặp nếu có
    print (f"Total authors to crawl: {len(start_urls)}")

    # start_urls = start_urls[0:2]

    # start_urls = [
    #     "https://www.thivien.net/Nguy%E1%BB%85n-Du/author-ZRyB2U-4oqfhcjZ7xrf1_A",
    # ]

    custom_settings = {
        # Giả lập Browser để tránh bị chặn
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 5, # Chậm lại 5s để lịch sự với server
    }

    
    count_authors = 0

    def parse(self, response):
        # --- 1. Xử lý phần Header (Thông tin tác giả) ---
        header = response.css('header.page-header h1')
        
        # Lấy bút danh (Text node trực tiếp của h1)
        main_name = header.xpath('./text()').get()
        if main_name:
            main_name = main_name.strip()
            
        # Lấy tên thật (nằm trong thẻ <small>)
        real_name = header.css('small::text').get()
        if real_name:
            real_name = real_name.strip()

        # --- 2. Xử lý Danh sách bài thơ ---
        poems_list = []
        
        # Chọn tất cả thẻ a nằm trong các khối .poem-group-list
        # Logic này lấy hết bài thơ bất kể nó nằm trong tập thơ nào
        for link in response.css('.poem-group-list a'):
            poem_title = link.css('::text').get()
            poem_href = link.css('::attr(href)').get()
            
            if poem_title and poem_href:
                full_url = response.urljoin(poem_href)
                poems_list.append({
                    'bai_tho': poem_title.strip(),
                    'url': full_url
                })

        # --- Output kết quả ---
        print(f"Crawled author: {main_name} ({real_name}), Total poems: {len(poems_list)}")
        
        self.count_authors += 1
        yield {
            'author_info': {
                'ten': main_name,
                'ten_that': real_name,
                'url': response.url,
            },
            'total_poems': len(poems_list),
            'poems': poems_list
        }
        if self.count_authors % 50 == 0:
            print(f"--- Processed {self.count_authors} authors so far ---")
            import time
            time.sleep(600)  # Nghỉ 10 giây sau mỗi 200 tác giả để tránh quá tải server

# --- Cấu hình để chạy trực tiếp bằng python ---
if __name__ == "__main__":
    # Cài đặt output ra file JSON
    process = CrawlerProcess(settings={
        'FEEDS': {
            'author_data.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True, # Ghi đè file cũ nếu chạy lại
            }
        },
        'LOG_LEVEL': 'INFO' # Chỉ hiện thông tin quan trọng, ẩn debug
    })

    process.crawl(ThivienAuthorSpider)
    process.start() # Bắt đầu crawl (blocking)  