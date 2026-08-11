import requests
import re
import json

url = "https://xn--gck1f423k.xn--1bvt37a.tools"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=10)
scripts = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)

for i, s in enumerate(scripts):
    if len(s) > 10000:
        print(f"--- Script index {i} (length: {len(s)}) ---")
        with open(f"scratch/script_{i}.js", "w", encoding="utf-8") as f:
            f.write(s)
        print(f"Saved scratch/script_{i}.js")
