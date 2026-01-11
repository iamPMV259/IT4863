import requests

url = "https://www.thivien.net/B%E1%BA%B1ng-Vi%E1%BB%87t/B%C3%A1ch-th%E1%BA%A3o/poem-AqbGn1tCLixW5ptMO7AtDA"

response = requests.get(url)

print(response.text)