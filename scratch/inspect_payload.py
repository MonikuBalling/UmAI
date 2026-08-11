import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://umamusume.jp/news/_payload.json", headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
})

with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    
print("Type of data:", type(data))
print("Length of data:", len(data))

# 文字列要素の中にニュースタイトルらしきものがあるか検索
for idx, item in enumerate(data):
    if isinstance(item, str) and ("ガチャ" in item or "更新" in item or "お知らせ" in item or "キャンペーン" in item or "育成" in item):
        print(f"Data[{idx}]: {item}")
