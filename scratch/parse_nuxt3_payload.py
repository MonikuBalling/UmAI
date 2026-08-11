import urllib.request
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://umamusume.jp/news/_payload.json", headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    raw_data = json.loads(resp.read().decode('utf-8'))

def resolve(val, data):
    if isinstance(val, int) and 0 <= val < len(data):
        return resolve(data[val], data)
    elif isinstance(val, dict):
        res = {}
        for k, v in val.items():
            res[k] = resolve(v, data)
        return res
    elif isinstance(val, list):
        return [resolve(v, data) for v in val]
    else:
        return val

# すべての文字列要素を出力
strings = [x for x in raw_data if isinstance(x, str)]
print("Strings count:", len(strings))

# 日付パターン (YYYY.MM.DD または YYYY/MM/DD) を含む文字列を検索
date_pattern = re.compile(r'\d{4}[\./]\d{2}[\./]\d{2}')
dates = [s for s in strings if date_pattern.search(s)]
print("Found dates:", dates)

# ニュースIDらしきものを検索
detail_urls = [s for s in strings if "detail" in s or "news" in s]
print("News strings:", detail_urls)

# 全文字列を出力してニュースタイトルを特定
for s in strings:
    if len(s) > 10 and ("ガチャ" in s or "開催" in s or "開始" in s or "キャンペーン" in s or "アプデ" in s or "更新" in s or "登場" in s or "不具合" in s or "について" in s or "お知らせ" in s):
        print("NEWS TITLE CANDIDATE:", s)
