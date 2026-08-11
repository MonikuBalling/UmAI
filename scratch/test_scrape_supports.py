import urllib.request
import urllib.parse
import json
import re

url = "https://ウマ娘.攻略.tools/supports"
encoded_url = urllib.parse.quote(url, safe=":/")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

req = urllib.request.Request(encoded_url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        print(f"HTML Length: {len(html)}")
        # サポートカードのリンクや画像を抽出
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html)
        print(f"Found {len(imgs)} images, {len(links)} links.")
        for img in imgs[:10]:
            print("IMG:", img)
except Exception as e:
    print(f"Error fetching URL: {e}")
