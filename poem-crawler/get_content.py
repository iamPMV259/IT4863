import json
import re
import time

import scrapy
from scrapy.crawler import CrawlerProcess
from w3lib.html import remove_tags


class PoemCrawler(scrapy.Spider):
    name = 'poem_crawler'
    
    urls = json.load(open('poem_urls.json', 'r', encoding='utf-8'))

    print(f"Total poem URLs to crawl: {len(urls)}")
    urls = urls[:10]
    start_urls = [item['url'] for item in urls]


    custom_settings = {
        'DOWNLOAD_DELAY': 5,
    }

  
    
    def clean_text(self, html_fragment):
        if not html_fragment:
            return ""
        text = re.sub(r'<br\s*/?>', '\n', html_fragment)
        text = remove_tags(text)
        text = text.replace(u'\xa0', ' ').strip()
        return text


    def parse(self, response):
        
        quoc_gia = response.css('.page-header .breadcrum a:nth-of-type(2) b::text').get()

        if quoc_gia != "Việt Nam":
            return

        ten_bai = response.css('.page-header h1::text').get()

        thoi_ky = response.css('.page-header .breadcrum a:nth-of-type(3) b::text').get()
        
        tac_gia = response.css('.page-header .breadcrum a:nth-of-type(4) b::text').get()

        tap_tho = response.css('.page-header .breadcrum a:nth-of-type(5) b::text').get()
        

        # print(f"Country: {quoc_gia}, Author: {tac_gia} for URL: {response.url}")

        the_tho = response.xpath('//div[@class="summary-section"]//a[contains(@href, "PoemType")]/text()').get()

        # print(f"--- Poem Type: {the_tho} ---")

        
        content = ""
        
        # --- KIỂM TRA: Đây có phải bài thơ Chữ Hán/Nôm có cấu trúc tách biệt không? ---
        # Cấu trúc này nằm trong div có class "poem-view-separated"
        separated_view = response.css('.poem-content .poem-view-separated')

        if separated_view:
            # === LOGIC XỬ LÝ BÀI THƠ CHỮ HÁN ===
            
            # Sử dụng XPath để chọn lọc thông minh:
            # 1. Chọn tất cả thẻ con trực tiếp (*) của .poem-view-separated
            # 2. Loại bỏ thẻ có class="han-chinese" (Nội dung chữ Hán)
            # 3. Loại bỏ thẻ mà BÊN TRONG nó có chứa class="han-chinese" (Tiêu đề chữ Hán thường nằm trong h4 > strong.han-chinese)
            # 4. Loại bỏ thẻ style="display:none" (Phần duplicate ẩn)
            
            nodes = separated_view.xpath('./*[not(@class="han-chinese") and not(descendant::*[@class="han-chinese"]) and not(contains(@style, "display:none"))]')
            
            parts = []
            for node in nodes:
                # Lấy raw html của từng node
                node_html = node.get()
                clean_str = self.clean_text(node_html)
                
                # Chỉ thêm vào danh sách nếu chuỗi không rỗng
                if clean_str:
                    parts.append(clean_str)
            
            # Nối các phần lại với nhau bằng xuống dòng
            content = "\n".join(parts)

        else:
            # === LOGIC CŨ CHO BÀI THƠ HIỆN ĐẠI/BÌNH THƯỜNG ===
            raw_html = response.css('.poem-content p').get()
            if raw_html:
                # Xóa thẻ sup (chú thích số [1])
                clean_html = re.sub(r'<sup.*?</sup>', '', raw_html)
                content = self.clean_text(clean_html)

        pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+')

        cleaned_text = pattern.sub('', content)
    
        # 2. Xử lý làm sạch lại (vì xóa chữ Hán sẽ để lại nhiều dòng trống thừa)
        # Xóa các dòng trắng liên tiếp (nhiều \n thành 1 \n)
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        
        # 3. Cắt khoảng trắng đầu đuôi
        content = cleaned_text.strip()


        


        yield {
            'url': response.url,
            'ten_bai': ten_bai.strip() if ten_bai else '',
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
            'poem_full_data_1.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True,
            }
        }
    })


    process.crawl(PoemCrawler)
    process.start()
