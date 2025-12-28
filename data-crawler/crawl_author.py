import json

import scrapy
from scrapy.crawler import CrawlerProcess


class ThivienAuthorSpider(scrapy.Spider):
    name = "thivien_author"
    
    authors_list = json.load(open('unique_authors.json', 'r', encoding='utf8'))
    
    start_urls = [author['url'] for author in authors_list]
    
    print (f"Total authors to crawl: {len(start_urls)}")


    custom_settings = {
        'DOWNLOAD_DELAY': 10,
    }

    
    count_authors = 0

    def parse(self, response):
        
        header = response.css('header.page-header h1')
        
        main_name = header.xpath('./text()').get()
        if main_name:
            main_name = main_name.strip()
            
        real_name = header.css('small::text').get()
        if real_name:
            real_name = real_name.strip()


        poems_list = []
        
        
        for link in response.css('.poem-group-list a'):
            poem_title = link.css('::text').get()
            poem_href = link.css('::attr(href)').get()
            
            if poem_title and poem_href:
                full_url = response.urljoin(poem_href)
                poems_list.append({
                    'bai_tho': poem_title.strip(),
                    'url': full_url
                })


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
            print(f"--- Processed {self.count_authors} authors ---")
            import time
            time.sleep(10)  
            
if __name__ == "__main__":
    
    process = CrawlerProcess(settings={
        'FEEDS': {
            'author_data.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True, 
            }
        }
    })

    process.crawl(ThivienAuthorSpider)
    process.start() 