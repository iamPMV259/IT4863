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
        'DOWNLOAD_DELAY': 10,
    }

    def parse(self, response):
        response.selector.remove_namespaces()

        items = response.xpath('//url')

        
        count = 0
        for item in items:
            link = item.xpath('./loc/text()').get()
            
            if link.find('.php') != -1:
                continue

            if link.find('poem') != -1:

                yield scrapy.Request(
                    url=link,
                    callback=self.parse_detail
                )

                time.sleep(5)
    
  


    def parse_detail(self, response):
        
        quoc_gia = response.css('.page-header .breadcrum a:nth-of-type(2) b::text').get()

        if quoc_gia != "Việt Nam":
            return

        thoi_ky = response.css('.page-header .breadcrum a:nth-of-type(3) b::text').get()
        
        tac_gia = response.css('.page-header .breadcrum a:nth-of-type(4) b::text').get()

        tap_tho = response.css('.page-header .breadcrum a:nth-of-type(5) b::text').get()
        


        the_tho = response.xpath('//div[@class="summary-section"]//a[contains(@href, "PoemType")]/text()').get()

    

        
        raw_html = response.css('.poem-content p').get()

        content = ""
        if raw_html:
            clean_html = re.sub(r'<sup.*?</sup>', '', raw_html)

            clean_html = re.sub(r'<br\s*/?>', '\n', clean_html)
            content = remove_tags(clean_html).strip()


        


        yield {
            'url': response.url,
            'quoc_gia': quoc_gia.strip() if quoc_gia else '',
            'tac_gia': tac_gia.strip() if tac_gia else '',
            'tap_tho': tap_tho.strip() if tap_tho else '',
            'thoi_ky': thoi_ky.strip() if thoi_ky else '',
            'the_tho': the_tho.strip() if the_tho else '',
            'noi_dung_tho': content,
        }





if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'poem_full_data.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
            }
        }
    })


    process.crawl(PoemCrawler)
    process.start()
