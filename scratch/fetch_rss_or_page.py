import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request("https://umamusume.jp/news/", headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        html = resp.read().decode('utf-8')
        # JavaScript内のデータソースを探す
        js_files = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
        print("JS Files:", js_files)
        
        # API URLがハードコードされていないか探す
        api_urls = re.findall(r'https?://[^\s"\']+/api/[^\s"\']+', html)
        print("API URLs in HTML:", api_urls)
except Exception as e:
    print("Error:", e)
