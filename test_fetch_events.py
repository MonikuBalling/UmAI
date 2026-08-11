import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def fetch_url(url_str):
    parsed = urllib.parse.urlparse(url_str)
    # netloc encoding
    netloc = parsed.netloc.encode('idna').decode('ascii')
    path = urllib.parse.quote(parsed.path)
    full_url = urllib.parse.urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))
    print(f"Decoded IDNA URL: {full_url}")
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            lines = [l.strip() for l in soup.get_text().splitlines() if l.strip()]
            print("=== Sample Lines ===")
            for line in lines[:30]:
                print(line)
    except Exception as e:
        print(f"Error: {e}")

fetch_url("https://ウマ娘.攻略.tools/race/vsevents/loh")
fetch_url("https://ウマ娘.攻略.tools/race/vsevents/chm")
