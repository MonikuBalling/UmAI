import urllib.request
import re
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://umamusume.jp/news/?t=game"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        html = resp.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.select('.news-list__item, li.news-list-item, div.news-item, a[href*="/news/detail"]')
        print(f"Found items: {len(items)}")
        
        # 正規表現で news/detail?id=... を検索
        matches = re.findall(r'href=["\'](/news/detail\?id=\d+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
        print(f"Regex matches: {len(matches)}")
        
        # インラインJSONスクリプトの検索
        json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html, re.DOTALL)
        if json_matches:
            print("Found __INITIAL_STATE__!")
        
        # ニュースタイトルのパターン抽出
        titles = re.findall(r'<p class="news-list-item__title">(.*?)</p>', html)
        dates = re.findall(r'<p class="news-list-item__date">(.*?)</p>', html)
        ids = re.findall(r'detail\?id=(\d+)', html)
        
        print(f"Titles: {len(titles)}, Dates: {len(dates)}, IDs: {len(ids)}")
        for i in range(min(5, len(ids))):
            t = titles[i] if i < len(titles) else "ニュース"
            d = dates[i] if i < len(dates) else "日付"
            print(f"[{d}] {t} -> https://umamusume.jp/news/detail?id={ids[i]}")

except Exception as e:
    print("HTML Error:", e)
