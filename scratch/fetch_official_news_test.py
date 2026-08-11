import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://umamusume.jp/api/ajax/news_list?news_type=game&page=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("API Response success! Items:", len(data.get("data", [])))
        for item in data.get("data", [])[:5]:
            title = item.get("title")
            posted_at = item.get("posted_at")
            news_id = item.get("news_id")
            article_url = f"https://umamusume.jp/news/detail?id={news_id}"
            print(f"[{posted_at}] {title} -> {article_url}")
except Exception as e:
    print("API Error:", e)
