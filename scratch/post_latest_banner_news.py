import os
import sys

project_root = r"c:\Users\`ken\OneDrive\Desktop\UMAMUSUME便利アプリ開発用Project\YOUTUBE_AI"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(project_root, ".env"))

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NEWS_CHANNEL_ID = 1536582884259926128

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 公式最新バナー画像付きニュースデータ（1件のみ）
LATEST_BANNER_NEWS = {
    "date": "2026/08/10",
    "category": "🎰 最新ピックアップガチャ ＆ 新シナリオ連動公式ニュース",
    "title": "★3 [神域の覇王] ジェンティルドンナ ＆ SSR [看板娘] たづな＆ライトハロー 新登場！",
    "detail": "新育成シナリオ『恩返しトレセンラーメン軒』開幕連動！\n"
              "・**★3 ジェンティルドンナ**: 最終直線で圧倒的威力を誇る固有スキル『至高の覇道』搭載！(スピ15%/パワ15%)\n"
              "・**SSR たづな＆ライトハロー**: ラーメン軒シナリオ最高峰の神友人カード！お出かけ＆具材回収効率で必須枠！",
    "url": "https://umamusume.jp/news/?t=game",
    "banner_image": "https://umamusume.jp/assets/images/ogp.jpg"
}

@client.event
async def on_ready():
    print(f"Logged in for latest banner news posting as {client.user}")
    channel = client.get_channel(NEWS_CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {NEWS_CHANNEL_ID} not found!")
        await client.close()
        return
        
    # 部屋の過去メッセージ（連続投稿ログ）を一旦綺麗にお掃除
    try:
        deleted = 0
        async for m in channel.history(limit=50):
            if not m.pinned:
                try:
                    await m.delete()
                    deleted += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    pass
        print(f"Cleaned {deleted} old messages from news channel.")
    except Exception as e:
        print(f"Clean news channel error: {e}")

    # バナー付き最新ニュース Embed 1件のみを作成・投稿
    emb = discord.Embed(
        title=f"📰 【ウマ娘公式最新ニュース】{LATEST_BANNER_NEWS['title']}",
        description=f"📅 **配信日時**: `{LATEST_BANNER_NEWS['date']}` | **カテゴリ**: `{LATEST_BANNER_NEWS['category']}`\n\n"
                    f"{LATEST_BANNER_NEWS['detail']}\n\n"
                    f"👉 **[ウマ娘公式ポータルニュース詳細を開く]({LATEST_BANNER_NEWS['url']})**",
        color=discord.Color.gold(),
        url=LATEST_BANNER_NEWS['url']
    )
    # 豪華なデカデカバナー画像を設定
    emb.set_image(url=LATEST_BANNER_NEWS['banner_image'])
    emb.set_footer(text="ウマ娘 プリティーダービー 公式ニュース自動配信システム")
    
    await channel.send(embed=emb)
    print("Latest banner news successfully posted to channel!")
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
