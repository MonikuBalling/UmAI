import requests
import re
import json
import os

url = "https://xn--gck1f423k.xn--1bvt37a.tools"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=10)
print(f"Status Code: {resp.status_code}")
print(f"Length: {len(resp.text)}")

# サポートカードのカード名・画像URL・タイプ・スキルを抽出
imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']+)["\']', resp.text)
if not imgs:
    # 属性順を逆にして抽出試行
    imgs = re.findall(r'<img[^>]+alt=["\']([^"\']+)["\'][^>]*src=["\']([^"\']+)["\']', resp.text)

print(f"Found {len(imgs)} cards with alt text!")
cards_data = []

for idx, item in enumerate(imgs[:30]):
    print(f"[{idx+1}] {item}")

with open("scratch/support_cards_sample.json", "w", encoding="utf-8") as f:
    json.dump(imgs, f, ensure_ascii=False, indent=2)

print("Saved sample JSON to scratch/support_cards_sample.json")
