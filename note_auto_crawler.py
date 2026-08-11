import os
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

NOTE_SOURCES_FILE = "data/note_learned_sources.json"

def search_and_crawl_note():
    """
    note上のウマ娘最新攻略・検証記事を自動巡回・探査し、
    執筆者・タイトル・URLをソース元情報としてデータベースへ自動記録・学習する関数
    """
    os.makedirs("data", exist_ok=True)
    
    existing = []
    if os.path.exists(NOTE_SOURCES_FILE):
        try:
            with open(NOTE_SOURCES_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    seen_urls = {item.get("url") for item in existing if item.get("url")}
    new_count = 0

    rss_urls = [
        f"https://note.com/hashtag/{urllib.parse.quote('ウマ娘')}/rss",
        "https://note.com/umamusume_sui/rss"
    ]

    for rss in rss_urls:
        try:
            req = urllib.request.Request(rss, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item'):
                title = item.findtext('title', 'ウマ娘攻略記事').strip()
                link = item.findtext('link', '').strip()
                creator = item.findtext('{http://purl.org/dc/elements/1.1/}creator', 'ウマ娘トレーナー').strip()
                
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    author_credit = f"{creator}様 (note)"
                    entry = {
                        "title": title,
                        "url": link,
                        "author": author_credit,
                        "author_url": link,
                        "memo": f"全自動巡回収集: {title[:30]}...",
                        "added_by": "全自動note巡回自己成長AI",
                        "date": "2026/08/11"
                    }
                    existing.insert(0, entry)
                    new_count += 1
                    
                    try:
                        import rag
                        rag.save_custom_correction(f"note検証({creator}様):{title}", f"参照URL:{link}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"[NOTE CRAWLER]: RSS fetch note ({rss}): {e}")

    if new_count > 0:
        with open(NOTE_SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"[NOTE AUTO CRAWLER] noteから新たに {new_count}件 のウマ娘攻略記事を全自動収集・データソース登録完了！")
    else:
        print("[NOTE AUTO CRAWLER] 新規note記事巡回完了 (既に最新状態です)")

    return new_count

if __name__ == "__main__":
    search_and_crawl_note()
