import requests
from pymongo import MongoClient

# 1. 抓取 HTML
url = "https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs"
r = requests.get(url)
html = r.text

# 2. 连接 MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["stockmarket"]
collection = db["SymbolDirectoryDefinitions"]

# 3. 存入数据库
doc = {
    "url": url,
    "html": html
}
collection.insert_one(doc)

print("✅ HTML 已存入 MongoDB")
