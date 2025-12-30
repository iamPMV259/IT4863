import json
import os
import time

import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess


class HustSmartSpider(scrapy.Spider):
    name = "hust_crawler_24h"
    start_urls = [
        "https://hust.edu.vn/vi/news/rss/",
        "https://hust.edu.vn/vi/news/rss/hoat-dong-chung/",
        "https://hust.edu.vn/vi/news/rss/cong-tac-dang-va-doan-the/",
        "https://hust.edu.vn/vi/news/rss/tuyen-sinh-dao-tao-cong-tac-sinh-vien/",
        "https://hust.edu.vn/vi/news/rss/khoa-hoc-cong-nghe-dmst/",
        "https://hust.edu.vn/vi/news/rss/hop-tac-doi-ngoai-truyen-thong/",
        "https://hust.edu.vn/vi/news/rss/kiem-dinh-xep-hang/",
        "https://hust.edu.vn/vi/news/rss/to-chuc-nhan-su-tuyen-dung/",
        "https://hust.edu.vn/vi/news/rss/bach-khoa-tren-bao-chi/",
        "https://hust.edu.vn/vi/news/rss/tin-tuc-su-kien/",
        "https://hust.edu.vn/vi/news/rss/tro-giup-can-bo/",
        "https://hust.edu.vn/vi/news/rss/tro-giup-sinh-vien/",
        "https://hust.edu.vn/vi/news/rss/su-kien-sap-dien-ra/",
        "https://hust.edu.vn/vi/news/rss/cong-tac-sinh-vien/",
        "https://hust.edu.vn/vi/news/rss/thong-bao-chung/",
        "https://hust.edu.vn/vi/news/rss/lich-cong-tac/",
    ]   
    
    data_file = 'ketqua_chitiet.json'
    
    data_store = {}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HustSmartSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf8') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        self.data_store = {item['url']: item for item in content if 'url' in item}
                    else:
                        self.data_store = {}
            except Exception as e:
                self.data_store = {}

    def spider_closed(self, spider):
        items_list = list(self.data_store.values())
        with open(self.data_file, 'w', encoding='utf8') as f:
            json.dump(items_list, f, ensure_ascii=False, indent=4)

    def parse(self, response):
        items = response.xpath('//channel/item')
        
        for item in items:
            link = item.xpath('link/text()').get()
            title_rss = item.xpath('title/text()').get()
            
            if link:
                link = link.strip()
                
                if link in self.data_store:
                    yield scrapy.Request(
                        url=link,
                        method='HEAD', 
                        callback=self.parse_check_modified,
                        meta={
                            'rss_title': title_rss,
                            'existing_item': self.data_store[link]
                        }
                    )
                else:
                    yield scrapy.Request(
                        url=link,
                        callback=self.parse_detail,
                        meta={'rss_title': title_rss}
                    )
                time.sleep(5)

    def parse_check_modified(self, response):
        
        server_last_modified = response.headers.get('Last-Modified', b'').decode('utf-8')
        
        existing_item = response.meta['existing_item']
        local_last_modified = existing_item.get('last_modified', '')

        if server_last_modified and server_last_modified != local_last_modified:
            
            
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_detail,
                meta=response.meta,
                dont_filter=True
            )
            
            

    def parse_detail(self, response):
        
        title = response.css('h1.title::text').get()
        if not title:
            title = response.meta.get('rss_title')

        content_raw = response.css('#news-bodyhtml *::text').getall()
        content_clean = " ".join([text.strip() for text in content_raw if text.strip()])
        
        last_modified = response.headers.get('Last-Modified', b'').decode('utf-8')

        item = {
            'title': title,
            'content': content_clean,
            'url': response.url,
            'last_modified': last_modified,
        }
        
        self.data_store[response.url] = item
        
        yield {
            'status': 'crawled', 
            'url': response.url
        }

if __name__ == "__main__":
    process = CrawlerProcess()

    process.crawl(HustSmartSpider)
    process.start()