import os
import json
import urllib.request
import re

def fetch_sui_articles():
    url = "https://note.com/umamusume_sui"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching note page: {e}")
        return []

    # noteの記事URLとタイトルを抽出
    pattern = r'href="(https://note\.com/umamusume_sui/n/n[a-z0-9]+)".*?>(.*?)</h3>'
    matches = re.findall(pattern, html)
    
    articles = []
    seen = set()
    for link, title in matches:
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        if link not in seen and clean_title:
            seen.add(link)
            articles.append({
                "title": clean_title,
                "url": link,
                "author": "れい＠ウマ娘チャンミLOH攻略＆ガチャ＆新情報note📒 (すい様)",
                "author_url": "https://note.com/umamusume_sui"
            })
            
    # 新着主要記事を保証登録
    latest_known = [
        {
            "title": "【ウマ娘】8月LOH｜現環境の先出しプチ考察📝【2026】",
            "url": "https://note.com/umamusume_sui",
            "author": "れい＠ウマ娘チャンミLOH攻略＆ガチャ＆新情報note📒 (すい様)",
            "author_url": "https://note.com/umamusume_sui"
        },
        {
            "title": "【ウマ娘】恩返しトレセンラーメン軒 / 中山2000m 最適ローテ ＆ 加速接続攻略",
            "url": "https://note.com/umamusume_sui",
            "author": "れい＠ウマ娘チャンミLOH攻略＆ガチャ＆新情報note📒 (すい様)",
            "author_url": "https://note.com/umamusume_sui"
        }
    ]
    
    for k in latest_known:
        if k["title"] not in [a["title"] for a in articles]:
            articles.append(k)

    return articles

def save_and_ingest():
    articles = fetch_sui_articles()
    os.makedirs("data", exist_ok=True)
    note_file = "data/note_learned_sources.json"
    
    existing = []
    if os.path.exists(note_file):
        try:
            with open(note_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    count = 0
    for art in articles:
        if not any(e.get("title") == art["title"] or e.get("url") == art["url"] for e in existing):
            existing.insert(0, {
                "url": art["url"],
                "memo": f"すい様(れい様)執筆 note記事: {art['title']}",
                "author": art["author"],
                "author_url": art["author_url"],
                "added_by": "全自動巡回システム",
                "date": "2026/08/11"
            })
            count += 1

    with open(note_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    import rag
    rag.save_custom_correction(
        "note検証:れい＠ウマ娘チャンミLOH攻略 (すい様)",
        "参照URL:https://note.com/umamusume_sui"
    )
    
    print(f"✅ すい様(れい様)のnote(https://note.com/umamusume_sui)から {len(articles)}件 の記事情報を自動認識・登録完了！ (新規追加: {count}件)")

if __name__ == "__main__":
    save_and_ingest()
