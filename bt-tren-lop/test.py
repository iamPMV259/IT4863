import requests

url = "https://hust.edu.vn/vi/news/tin-tuc-su-kien/co-giao-bach-khoa-nay-so-de-tai-nghien-cuu-khoa-hoc-655715.html"

res = requests.get(url, timeout=30)

print(res.status_code)

res_head = requests.head(url, timeout=30)

print(res_head.status_code)
print(res_head.headers.get('last-modified'))
# print(res_head.headers)