import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

req = urllib.request.Request("https://umamusume.jp/news/_payload.json", headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        content = resp.read().decode('utf-8')
        data = json.loads(content)
        print("Payload JSON loaded successfully!")
        
        # ニュース項目を解析
        news_list = []
        if isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict):
                    title = obj.get("title") or obj.get("news_title")
                    id_val = obj.get("id") or obj.get("news_id")
                    posted_at = obj.get("posted_at") or obj.get("date")
                    if title and id_val:
                        news_list.append({
                            "title": title,
                            "id": id_val,
                            "date": posted_at,
                            "url": f"https://umamusume.jp/news/detail?id={id_val}"
                        })
        print(f"Parsed news items: {len(news_list)}")
        for n in news_list[:10]:
            print(f"[{n['date']}] {n['title']} -> {n['url']}")
            
except Exception as e:
    print("Payload Error:", e)
