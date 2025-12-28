

import scrapy
from scrapy.crawler import CrawlerProcess


class HustRssSpider(scrapy.Spider):
    name = "hust_rss"
    start_urls = [
        "https://hust.edu.vn/vi/news/rss/"

    ]

    def parse(self, response):
        items = response.xpath('//channel/item')
        for item in items:
            yield {
                'title': item.xpath('title/text()').get(),
                'link': item.xpath('link/text()').get()
            }

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'ketqua_rss.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True, 
            },
        },
    })

    process.crawl(HustRssSpider)
    process.start() 