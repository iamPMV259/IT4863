import scrapy
from scrapy.crawler import CrawlerProcess


class ThivienAuthorListSpider(scrapy.Spider):
    name = "thivien_author_list"
    
    # URL trang danh sách tác giả (Page 4)
    start_urls = [
        "https://www.thivien.net/search-author.php?Country=2&Age%5B%5D=52",
        "https://www.thivien.net/search-author.php?Country=2&Age[]=52&Page=2"
    ]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
    }

    def parse(self, response):
        # Lặp qua từng khối item chứa thông tin tác giả
        # Class "list-item" bao bọc toàn bộ thông tin của 1 dòng
        for item in response.css('.list-item'):
            
            # Tìm thẻ <a> bên trong thẻ <h4 class="list-item-header">
            author_link = item.css('.list-item-header a')
            
            name = author_link.css('::text').get()
            href = author_link.css('::attr(href)').get()

            # Chỉ lấy dữ liệu nếu tìm thấy cả tên và link
            if name and href:
                yield {
                    'tác giả': name.strip(),
                    'url': response.urljoin(href) # Chuyển link tương đối thành tuyệt đối
                }


async def print_author_list():
    process = CrawlerProcess(settings={
        'FEEDS': {
            'authors_list.json': { # Tên file output
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True,
            }
        },
        'LOG_LEVEL': 'INFO'
    })

    process.crawl(ThivienAuthorListSpider)
    process.start()



class ThivienAuthorSpider(scrapy.Spider):
    name = "thivien_author"
    
    # URL tác giả bạn cung cấp
    start_urls = [
        'https://www.thivien.net/B%E1%BA%B1ng-Vi%E1%BB%87t/author-aMN7s3bVCOu89mMWzbg_Kg'
    ]

    custom_settings = {
        # Giả lập Browser để tránh bị chặn
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1, # Chậm lại 1s để lịch sự với server
    }

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
        yield {
            'author_info': {
                'ten': main_name,
                'ten_that': real_name
            },
            'total_poems': len(poems_list),
            'poems': poems_list
        }


if __name__ == "__main__":