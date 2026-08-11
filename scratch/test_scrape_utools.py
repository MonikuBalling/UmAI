import requests
import re
import json

url = "https://xn--1bvt37a.tools/supports"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Content Length: {len(resp.text)}")
    
    # HTMLからカードデータや画像を抽出
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', resp.text)
    print(f"Total Images: {len(imgs)}")
    for img in imgs[:15]:
        print("IMG:", img)
        
    with open("scratch/utools_supports.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved HTML successfully!")
except Exception as e:
    print(f"Fetch Error: {e}")
