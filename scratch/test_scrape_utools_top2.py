import requests
import re

url = "https://xn--1bvt37a.tools/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=10)
links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', resp.text)
print("=== All Links ===")
for l in links[:30]:
    print("LINK:", l)
