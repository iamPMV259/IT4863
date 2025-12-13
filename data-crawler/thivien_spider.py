import json
import random

import scrapy
from scrapy.crawler import CrawlerProcess

name_file = "part_1"

class ThivienSpider(scrapy.Spider):
    name = 'thivien'
    allowed_domains = ['thivien.net']
    
    def __init__(self, *args, **kwargs):
        super(ThivienSpider, self).__init__(*args, **kwargs)
        urls_list = json.load(open(f'poem_urls_list_{name_file}.json', 'r', encoding='utf-8'))
        self.start_urls = [item['url'] for item in urls_list]
        self.count = 0
    
    def parse(self, response):
        """
        Parse poem page and extract required data
        """
        if response.css('.poem-content'):
            # Lấy nội dung bài thơ từ class="poem-content"
            poem_content = response.css('.poem-content').get()
            
            # Nếu muốn lấy text thuần túy không có HTML tags
            # Lấy tất cả text nodes bên trong poem-content
            poem_content_lines = response.css('.poem-content *::text, .poem-content::text').getall()
            # Loại bỏ các dòng trống và strip whitespace
            poem_content_lines = [line.strip() for line in poem_content_lines if line.strip()]
            poem_content_text_full = '\n'.join(poem_content_lines)
            
            # Lấy toàn bộ HTML bên trong poem-content (bao gồm cả các tag con)
            poem_content_html = response.css('.poem-content').extract_first()
        else:
            # Lấy nội dung bài thơ từ class="post-content"
            poem_content = response.css('.post-content').get()
            
            # Nếu muốn lấy text thuần túy không có HTML tags
            # Lấy tất cả text nodes bên trong post-content
            poem_content_lines = response.css('.post-content *::text, .post-content::text').getall()
            # Loại bỏ các dòng trống và strip whitespace
            poem_content_lines = [line.strip() for line in poem_content_lines if line.strip()]
            poem_content_text_full = '\n'.join(poem_content_lines)
            
            # Lấy toàn bộ HTML bên trong post-content (bao gồm cả các tag con)
            poem_content_html = response.css('.post-content').extract_first()
        
        # Lấy thông tin Thể thơ
        the_tho = None
        # Method 1: Tìm text "Thể thơ:" và lấy link sau nó
        the_tho_link = response.xpath('//text()[contains(., "Thể thơ:")]/following-sibling::a[1]/text()').get()
        if the_tho_link:
            the_tho = the_tho_link.strip()
        
        # Method 2: Fallback - tìm trong summary-section
        if not the_tho:
            the_tho = response.xpath('//div[@class="summary-section"]//a[contains(@href, "PoemType")]/text()').get()
            if the_tho:
                the_tho = the_tho.strip()
        
        # Lấy thông tin Thời kỳ
        thoi_ky = None
        # Method 1: Tìm text "Thời kỳ:" và lấy link sau nó
        thoi_ky_link = response.xpath('//text()[contains(., "Thời kỳ:")]/following-sibling::a[1]/text()').get()
        if thoi_ky_link:
            thoi_ky = thoi_ky_link.strip()
        
        # Method 2: Fallback - tìm trong summary-section
        if not thoi_ky:
            thoi_ky = response.xpath('//div[@class="summary-section"]//a[contains(@href, "Age")]/text()').get()
            if thoi_ky:
                thoi_ky = thoi_ky.strip()
        
        # Lấy tên bài thơ (optional - thông tin bổ sung)
        poem_title = response.css('h1::text').get()
        if not poem_title:
            poem_title = response.xpath('//h1/text()').get()
        if poem_title:
            poem_title = poem_title.strip()
        
        # Lấy tên tác giả (optional - thông tin bổ sung)
        # Tác giả thường là link cuối cùng trong breadcrumb
        author = response.xpath('//p[@class="breadcrum"]/a[last()]/b/text()').get()
        if not author:
            author = response.css('p.breadcrum a:last-child b::text').get()
        if author:
            author = author.strip()
        
        # Tạo dictionary chứa tất cả dữ liệu
        poem_data = {
            'url': response.url,
            'poem_title': poem_title,
            'author': author,
            'poem_content_html': poem_content_html,
            'poem_content_text': poem_content_text_full,
            'the_tho': the_tho,
            'thoi_ky': thoi_ky,
        }
        print(f"Scraped poem: {poem_title} by {author}")
        print("-" * 40)
        self.count += 1
        if self.count % 100 == 0:
            print(f"Scraped {self.count} poems so far.")
            import time
            time.sleep(600)  # Tạm dừng 10 phút sau mỗi 100 bài thơ để tránh bị block
        
        yield poem_data


# Cấu hình và chạy spider
if __name__ == '__main__':
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'FEEDS': {
            f'thivien_poems_{name_file}.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'ensure_ascii': False,
                'indent': 4,
            },
            f'thivien_poems_{name_file}.csv': {
                'format': 'csv',
                'encoding': 'utf-8',
            },
        },
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': random.uniform(30, 60),  # Delay 5 giây giữa các request để tránh bị block
    })
    
    process.crawl(ThivienSpider)
    process.start()