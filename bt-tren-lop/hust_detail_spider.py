

import json
import time

import scrapy
from scrapy.crawler import CrawlerProcess


class HustDetailSpider(scrapy.Spider):
    name = "hust_detail"
    
    urls = json.load(open("ketqua_rss.json", "r", encoding="utf-8"))
    start_urls = [item['link'] for item in urls]

    def parse(self, response):
        
        title = response.css('h1.title::text').get()

        
        content_raw = response.css('#news-bodyhtml *::text').getall()
        
        content_clean = " ".join([text.strip() for text in content_raw if text.strip()])
      
        

        yield {
            'title': title,
            'content_length': len(content_clean), 
            'content': content_clean,
            'url': response.url
        }
        time.sleep(5)

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'ketqua_chitiet.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True,
            },
        },
    })

    process.crawl(HustDetailSpider)
    process.start()