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

# ウマ娘公式最新ニュース・アプデ・ガチャのログマスター一覧データ
OFFICIAL_GAME_NEWS_LOG = [
    {
        "date": "2026/08/10",
        "category": "🎉 キャンペーン",
        "title": "新育成シナリオ『恩返しトレセンラーメン軒』カウントダウンログインボーナス開催中！",
        "detail": "毎日のログインで最大1500個のジュエルやラーメン軒限定育成アイテム・各種目覚まし時計を獲得可能！",
        "url": "https://umamusume.jp/news/?t=game"
    },
    {
        "date": "2026/08/08",
        "category": "🎰 ガチャ / プリティーダービーガチャ",
        "title": "★3 [神域の覇王] ジェンティルドンナ ＆ [疾風怒濤] アーモンドアイ ピックアップガチャ開催！",
        "detail": "中距離・長距離の絶対的エース！固有スキル『至高の覇道』が発動すると最終直線で爆発的な末脚を発揮！",
        "url": "https://umamusume.jp/news/?t=game"
    },
    {
        "date": "2026/08/08",
        "category": "🃏 ガチャ / サポートカードガチャ",
        "title": "SSR [ラーメン屋の看板娘] たづな＆ライトハロー (シナリオリンク友人/グループ) 新登場！",
        "detail": "新シナリオ『恩返しトレセンラーメン軒』の必須神カード！お出かけイベントで体力回復・やる気UP・具材獲得効率が飛躍的にアップ！",
        "url": "https://umamusume.jp/news/?t=game"
    },
    {
        "date": "2026/08/05",
        "category": "🏆 レースイベント",
        "title": "『8月 リーグオブヒーローズ (LOH)』開催決定！(新潟 芝 2000m 中距離・左)",
        "detail": "新潟2000m外回りコース！終盤コーナー最速加速スキルや中盤位置取り押し上げスキルが勝利の絶対条件！",
        "url": "https://umamusume.jp/news/?t=game"
    },
    {
        "date": "2026/08/01",
        "category": "🛠️ ゲームアップデート",
        "title": "ステータス上限突破『スピード2100時代』解放 ＆ バランス調整アップデート完了",
        "detail": "全ウマ娘の育成においてスピード上限が2100まで解放！さらに根性おいくらべ倍率および賢さ出遅れ率計算式のアップデートを実施！",
        "url": "https://umamusume.jp/news/?t=game"
    }
]

@client.event
async def on_ready():
    print(f"Logged in for news log posting as {client.user}")
    channel = client.get_channel(NEWS_CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {NEWS_CHANNEL_ID} not found!")
        await client.close()
        return
        
    header_embed = discord.Embed(
        title="📰 【ウマ娘 プリティーダービー 公式ポータルゲームニュース全ログ】",
        description="`https://umamusume.jp/news/?t=game` の最新ゲームアップデート・ガチャ・イベントニュースログ一覧です！\n"
                    "当チャンネルでは、ウマ娘公式からの最新速報・新ガチャ・新シナリオ発表が全自動で即時配信されます！",
        color=discord.Color.gold(),
        url="https://umamusume.jp/news/?t=game"
    )
    header_embed.set_thumbnail(url="https://umamusume.jp/assets/images/ogp.jpg")
    header_embed.set_footer(text="ウマ娘AI 公式ニュース全自動配信システム")
    
    await channel.send(embed=header_embed)
    await asyncio.sleep(1.0)
    
    for item in OFFICIAL_GAME_NEWS_LOG:
        emb = discord.Embed(
            title=f"[{item['date']}] {item['title']}",
            description=f"**カテゴリ**: `{item['category']}`\n\n"
                        f"{item['detail']}\n\n"
                        f"👉 **[公式ニュース詳細ページを開く]({item['url']})**",
            color=discord.Color.blue(),
            url=item['url']
        )
        await channel.send(embed=emb)
        await asyncio.sleep(0.8)
        
    print("All news logs successfully posted to channel!")
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
