import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://umamusume.jp/news/?t=game'
}

endpoints = [
    "https://umamusume.jp/api/ajax/news_list?news_type=game",
    "https://umamusume.jp/api/ajax/news_list?announce_type=game",
    "https://umamusume.jp/news/api/list?type=game",
    "https://umamusume.jp/news/api/get_list?t=game",
    "https://umamusume.jp/api/news/list?t=game"
]

for ep in endpoints:
    try:
        req = urllib.request.Request(ep, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"SUCCESS {ep} -> {len(data)}")
    except Exception as e:
        print(f"FAIL {ep} -> {e}")
