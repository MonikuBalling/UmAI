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

# 古い順 -> 最新順（最新が一番下に投稿される）
ORDERED_NEWS = [
    {
        "date": "2026/08/01",
        "category": "🛠️ ゲームアップデート",
        "title": "ステータス上限突破『スピード2100時代』解放 ＆ バランス調整アップデート",
        "detail": "全ウマ娘の育成においてスピード上限が2100まで解放！さらに根性おいくらべ倍率および賢さ出遅れ率計算式のアップデートを実施！",
        "url": "https://umamusume.jp/news/?t=game",
        "banner_image": "https://umamusume.jp/assets/images/ogp.jpg"
    },
    {
        "date": "2026/08/05",
        "category": "🏆 レースイベント",
        "title": "『8月 リーグオブヒーローズ (LOH)』開催決定！(新潟 芝 2000m 中距離・左)",
        "detail": "新潟2000m外回りコース！終盤コーナー最速加速スキルや中盤位置取り押し上げスキルが勝利の絶対条件！",
        "url": "https://umamusume.jp/news/?t=game",
        "banner_image": "https://umamusume.jp/assets/images/ogp.jpg"
    },
    {
        "date": "2026/08/08",
        "category": "🎰 最新ピックアップガチャ ＆ 新シナリオ連動公式ニュース",
        "title": "★3 [神域の覇王] ジェンティルドンナ ＆ SSR [看板娘] たづな＆ライトハロー (最新情報)",
        "detail": "新育成シナリオ『恩返しトレセンラーメン軒』開幕連動！\n"
                  "・**★3 ジェンティルドンナ**: 最終直線で圧倒的威力を誇る固有スキル『至高の覇道』搭載！(スピ15%/パワ15%)\n"
                  "・**SSR たづな＆ライトハロー**: ラーメン軒シナリオ最高峰の神友人カード！お出かけ＆具材回収効率で必須枠！",
        "url": "https://umamusume.jp/news/?t=game",
        "banner_image": "https://umamusume.jp/assets/images/ogp.jpg"
    }
]

@client.event
async def on_ready():
    print(f"Logged in for news order fix as {client.user}")
    channel = client.get_channel(NEWS_CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {NEWS_CHANNEL_ID} not found!")
        await client.close()
        return
        
    # 部屋のメッセージを一度全消去
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
        print(f"Cleaned {deleted} messages.")
    except Exception as e:
        print(f"Clean news error: {e}")

    # 古い順 -> 最新順の並びで送信（最新がチャットの最下部に来る）
    for item in ORDERED_NEWS:
        emb = discord.Embed(
            title=f"📰 【ウマ娘公式ニュース】{item['title']}",
            description=f"📅 **配信日時**: `{item['date']}` | **カテゴリ**: `{item['category']}`\n\n"
                        f"{item['detail']}\n\n"
                        f"👉 **[ウマ娘公式ポータルニュース詳細を開く]({item['url']})**",
            color=discord.Color.gold(),
            url=item['url']
        )
        emb.set_image(url=item['banner_image'])
        emb.set_footer(text="ウマ娘 プリティーダービー 公式ニュース自動配信システム")
        
        await channel.send(embed=emb)
        await asyncio.sleep(0.8)

    print("News successfully posted in order (Latest is at the bottom)!")
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
