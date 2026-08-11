import requests
import re
import json

url = "https://xn--t8j4d8b0b3b4d.xn--qck0e2a.tools/supports"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Content Length: {len(resp.text)}")
    
    # 画像とリンク
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', resp.text)
    print(f"Total Images: {len(imgs)}")
    for img in imgs[:15]:
        print("IMG:", img)
        
    with open("scratch/supports_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved HTML to scratch/supports_page.html")
except Exception as e:
    print(f"Requests Error: {e}")
