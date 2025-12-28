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
        if response.css('.poem-content'):
            
            poem_content = response.css('.poem-content').get()
            
            
            poem_content_lines = response.css('.poem-content *::text, .poem-content::text').getall()
            
            poem_content_lines = [line.strip() for line in poem_content_lines if line.strip()]
            poem_content_text_full = '\n'.join(poem_content_lines)
            
            
            poem_content_html = response.css('.poem-content').extract_first()
        
        
        
        the_tho = None
        
        the_tho_link = response.xpath('//text()[contains(., "Thể thơ:")]/following-sibling::a[1]/text()').get()
        if the_tho_link:
            the_tho = the_tho_link.strip()
        
        
        if not the_tho:
            the_tho = response.xpath('//div[@class="summary-section"]//a[contains(@href, "PoemType")]/text()').get()
            if the_tho:
                the_tho = the_tho.strip()
        
        
        thoi_ky = None
        
        thoi_ky_link = response.xpath('//text()[contains(., "Thời kỳ:")]/following-sibling::a[1]/text()').get()
        if thoi_ky_link:
            thoi_ky = thoi_ky_link.strip()
        
        
        if not thoi_ky:
            thoi_ky = response.xpath('//div[@class="summary-section"]//a[contains(@href, "Age")]/text()').get()
            if thoi_ky:
                thoi_ky = thoi_ky.strip()
        
        
        poem_title = response.css('h1::text').get()
        if not poem_title:
            poem_title = response.xpath('//h1/text()').get()
        if poem_title:
            poem_title = poem_title.strip()
        
        
        author = response.xpath('//p[@class="breadcrum"]/a[last()]/b/text()').get()
        if not author:
            author = response.css('p.breadcrum a:last-child b::text').get()
        if author:
            author = author.strip()
            
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
            time.sleep(600)  
        
        yield poem_data


if __name__ == '__main__':
    process = CrawlerProcess(settings={
        'FEEDS': {
            f'thivien_poems_{name_file}.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'ensure_ascii': False,
                'indent': 4,
            },
        },
        'DOWNLOAD_DELAY': random.uniform(30, 60), 
    })
    
    process.crawl(ThivienSpider)
    process.start()
