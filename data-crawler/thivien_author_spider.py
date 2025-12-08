import scrapy
from scrapy.crawler import CrawlerProcess


class ThivienAuthorSpider(scrapy.Spider):
    """
    Spider để crawl trang tác giả thivien.net và lấy:
    - Thông tin tác giả (tên, tên thật, giới tính)
    - Danh sách TẤT CẢ bài thơ của tác giả
    """
    name = 'thivien_author'
    allowed_domains = ['thivien.net']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, author_url=None, *args, **kwargs):
        super(ThivienAuthorSpider, self).__init__(*args, **kwargs)
        
        if author_url:
            self.start_urls = [author_url]
        else:
            # URL mặc định - Bằng Việt
            self.start_urls = [
                'https://www.thivien.net/B%E1%BA%B1ng-Vi%E1%BB%87t/author-aMN7s3bVCOu89mMWzbg_Kg'
            ]
    
    def parse(self, response):
        """Parse author page"""
        self.logger.info(f'Crawling author page: {response.url}')
        
        # 1. Lấy thông tin tác giả
        author_info = self.extract_author_info(response)
        
        # 2. Lấy danh sách TẤT CẢ bài thơ
        poems_list = self.extract_poems_list(response)
        
        # 3. Tổng hợp dữ liệu
        author_data = {
            'url': response.url,
            'author_info': author_info,
            'poems': {
                'total': len(poems_list),
                'list': poems_list,
            },
            'crawled_at': scrapy.utils.time.datetime.now().isoformat(),
        }
        
        yield author_data
    
    def extract_author_info(self, response):
        """
        Trích xuất thông tin tác giả từ header
        
        HTML Structure:
        <header class="page-header">
            <h1>Bằng Việt <small>Nguyễn Việt Bằng</small> <sup><i class="fa fa-mars"></i></sup></h1>
            <p class="breadcrum">
                <a><b>Thơ</b></a> » 
                <a><b>Việt Nam</b></a> » 
                <a><b>Hiện đại</b></a>
            </p>
        </header>
        """
        info = {}
        
        # Lấy tên tác giả (text trực tiếp trong h1, bỏ qua <small>)
        # Method: Lấy text node đầu tiên của h1
        author_name = response.xpath('//header[@class="page-header"]/h1/text()[1]').get()
        if author_name:
            info['ten'] = author_name.strip()
        else:
            info['ten'] = None
        
        # Lấy tên thật (trong <small>)
        real_name = response.css('header.page-header h1 small::text').get()
        if real_name:
            info['ten_that'] = real_name.strip()
        else:
            info['ten_that'] = None
        
        # Lấy giới tính (từ icon)
        if response.css('header.page-header h1 sup i.fa-mars'):
            info['gioi_tinh'] = 'Nam'
        elif response.css('header.page-header h1 sup i.fa-venus'):
            info['gioi_tinh'] = 'Nữ'
        else:
            info['gioi_tinh'] = None
        
        # Lấy quốc gia và thời kỳ từ breadcrumb
        breadcrumb_texts = response.css('p.breadcrum a b::text').getall()
        if len(breadcrumb_texts) >= 2:
            # breadcrumb_texts[0] = "Thơ"
            # breadcrumb_texts[1] = "Việt Nam"
            # breadcrumb_texts[2] = "Hiện đại"
            info['quoc_gia'] = breadcrumb_texts[1] if len(breadcrumb_texts) > 1 else None
            info['thoi_ky'] = breadcrumb_texts[2] if len(breadcrumb_texts) > 2 else None
        else:
            info['quoc_gia'] = None
            info['thoi_ky'] = None
        
        return info
    
    def extract_poems_list(self, response):
        """
        Trích xuất danh sách tất cả bài thơ
        
        HTML Structure:
        <ol>
            <li><a href="/url">Bài thơ 1</a></li>
            <li><a href="/url">Bài thơ 2</a> 16</li>
            ...
        </ol>
        
        Note: Có số ở cuối một số bài thơ (lượt thích/comment)
        """
        poems = []
        
        # Lấy tất cả <li> trong <ol>
        poem_items = response.css('ol > li')
        
        self.logger.info(f'Found {len(poem_items)} poem items')
        
        for item in poem_items:
            poem = {}
            
            # Lấy link và tên bài thơ
            poem_link = item.css('a::attr(href)').get()
            poem_title = item.css('a::text').get()
            
            if poem_link:
                poem['url'] = response.urljoin(poem_link)
            else:
                poem['url'] = None
            
            if poem_title:
                poem['bai_tho'] = poem_title.strip()
            else:
                poem['bai_tho'] = None
            
            # Lấy số lượt thích/interact (số cuối cùng trong li)
            # Ví dụ: <li><a>Bếp lửa</a> 16</li>
            all_text = item.css('::text').getall()
            luot_thich = None
            for text in reversed(all_text):
                text = text.strip()
                if text and text.isdigit():
                    luot_thich = int(text)
                    break
            poem['luot_thich'] = luot_thich
            
            poems.append(poem)
        
        return poems


def run_author_spider(author_url=None, output_file='author_poems.json'):
    """
    Function để chạy author spider
    
    Args:
        author_url: URL trang tác giả
        output_file: Tên file output
    """
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'FEEDS': {
            output_file: {
                'format': 'json',
                'encoding': 'utf-8',
                'ensure_ascii': False,
                'indent': 4,
                'overwrite': True,
            },
        },
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
    })
    
    process.crawl(ThivienAuthorSpider, author_url=author_url)
    process.start()


if __name__ == '__main__':
    # Crawl trang tác giả Bằng Việt
    author_url = 'https://www.thivien.net/B%E1%BA%B1ng-Vi%E1%BB%87t/author-aMN7s3bVCOu89mMWzbg_Kg'
    
    print("="*80)
    print("THIVIEN AUTHOR SPIDER")
    print("="*80)
    print(f"\nCrawling: {author_url}")
    print(f"Output: bang_viet_poems.json\n")
    
    run_author_spider(author_url=author_url, output_file='bang_viet_poems.json')
    
    print("\n" + "="*80)
    print("✅ DONE! Check bang_viet_poems.json for results")
    print("="*80)