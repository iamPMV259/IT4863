import json
import re
import time

import scrapy
from scrapy.crawler import CrawlerProcess
from w3lib.html import remove_tags


class PoemCrawler(scrapy.Spider):
    name = 'poem_crawler'
    
    start_urls = [
        'file:///home/pmv259/Downloads/_sitemap1.xml',
        'file:///home/pmv259/Downloads/_sitemap2.xml',
        'file:///home/pmv259/Downloads/_sitemap3.xml',
        'file:///home/pmv259/Downloads/_sitemap4.xml',
        'file:///home/pmv259/Downloads/_sitemap5.xml',
    ]


    custom_settings = {
        'DOWNLOAD_DELAY': 5,
    }

    def parse(self, response):
        response.selector.remove_namespaces()

        items = response.xpath('//url')

        print(f"Found {len(items)} items in sitemap: {response.url}")
        
        count = 0
        for item in items:
            link = item.xpath('./loc/text()').get()
            
            if link.find('.php') != -1:
                continue

            if link.find('poem') != -1:

                yield {
                    'url': link,
                }
    






if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'poem_urls.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True,
            }
        }
    })


    process.crawl(PoemCrawler)
    process.start()
