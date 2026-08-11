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
with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    html = resp.read().decode('utf-8')

js_files = re.findall(r'src=["\'](/_nuxt/js/[^"\']+)["\']', html)
print("Found JS files:", js_files)

for js_path in js_files:
    full_js_url = f"https://umamusume.jp{js_path}"
    try:
        jreq = urllib.request.Request(full_js_url, headers=headers)
        with urllib.request.urlopen(jreq, context=ctx, timeout=5) as jresp:
            jcode = jresp.read().decode('utf-8')
            print(f"Loaded {js_path} (len: {len(jcode)})")
            # /api/ や /news/ や fetch の文字を探す
            apis = re.findall(r'["\'](/api/[^"\']+)["\']', jcode)
            apis += re.findall(r'["\'](https?://[^\s"\']+)["\']', jcode)
            for a in apis:
                if "news" in a or "announce" in a or "game" in a:
                    print("  Found API candidate:", a)
    except Exception as e:
        print(f"Error loading {js_path}: {e}")
