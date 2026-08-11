import sys
import asyncio
from playwright.async_api import async_playwright

async def fetch_news():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to https://umamusume.jp/news/?t=game ...")
        await page.goto("https://umamusume.jp/news/?t=game", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # ネットワークリクエストのキャプチャまたはDOM要素の取得
        news_items = await page.evaluate('''() => {
            const results = [];
            const links = document.querySelectorAll('a[href*="/news/detail"]');
            links.forEach(a => {
                const text = a.innerText || a.textContent;
                const href = a.getAttribute('href');
                results.append ? results.append({text, href}) : results.push({text, href});
            });
            return results;
        }''')
        
        print(f"Extracted {len(news_items)} news items!")
        for item in news_items[:10]:
            print(f"Item: {item['text'].strip().replace(chr(10), ' ')} -> https://umamusume.jp{item['href']}")
            
        await browser.close()
        return news_items

if __name__ == "__main__":
    asyncio.run(fetch_news())
