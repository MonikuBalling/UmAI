import requests
import re
import json

url = "https://xn--gck1f423k.xn--1bvt37a.tools"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=10)
html = resp.text

# NEXT.JS や Vue / JS変数をサーチ
next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if next_data:
    data = json.loads(next_data.group(1))
    with open("scratch/next_data_supports.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Found NEXT_DATA and saved to scratch/next_data_supports.json!")
else:
    print("No NEXT_DATA, searching for inline script JSON...")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(scripts):
        if "SSR" in s or "スピード" in s or "support" in s:
            print(f"Script {i} contains keywords! Length: {len(s)}")
