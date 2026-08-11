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

# 本当に最新の1件のみ
SINGLE_LATEST_NEWS = {
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
    print(f"Logged in for single latest news enforcement as {client.user}")
    channel = client.get_channel(NEWS_CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {NEWS_CHANNEL_ID} not found!")
        await client.close()
        return
        
    # 部屋の過去メッセージを全て全消去して完全に1通にする準備
    try:
        deleted = 0
        async for m in channel.history(limit=100):
            if not m.pinned:
                try:
                    await m.delete()
                    deleted += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    pass
        print(f"Deleted {deleted} messages from news channel.")
    except Exception as e:
        print(f"Clean error: {e}")

    # 本当に最新の1通のみをバナー付きで送信
    emb = discord.Embed(
        title=f"📰 【ウマ娘公式最新ニュース】{SINGLE_LATEST_NEWS['title']}",
        description=f"📅 **配信日時**: `{SINGLE_LATEST_NEWS['date']}` | **カテゴリ**: `{SINGLE_LATEST_NEWS['category']}`\n\n"
                    f"{SINGLE_LATEST_NEWS['detail']}\n\n"
                    f"👉 **[ウマ娘公式ポータルニュース詳細を開く]({SINGLE_LATEST_NEWS['url']})**",
        color=discord.Color.gold(),
        url=SINGLE_LATEST_NEWS['url']
    )
    emb.set_image(url=SINGLE_LATEST_NEWS['banner_image'])
    emb.set_footer(text="ウマ娘 プリティーダービー 公式ニュース自動配信システム")
    
    await channel.send(embed=emb)
    print("Single latest news posted. Channel clean complete!")
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
