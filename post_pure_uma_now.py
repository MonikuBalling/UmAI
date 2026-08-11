import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1536523629708451941
IMAGE_PATH = r"C:\Users\`ken\OneDrive\Desktop\UMAMUSUME便利アプリ開発用Project\YOUTUBE_AI\pure_umamusume_only.png"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Logged in as", client.user)
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        for guild in client.guilds:
            for ch in guild.text_channels:
                if "ルームマッチ" in ch.name or "分析" in ch.name:
                    channel = ch
                    break

    if channel:
        # 古い全体スクショ付きメッセージを検索して削除試行
        try:
            async for msg in channel.history(limit=5):
                if msg.author == client.user and "リアルタイムアナライズ" in msg.content:
                    await msg.delete()
                    print("Deleted old full screenshot message!")
                    break
        except Exception:
            pass

        report_text = (
            "🏁 **【ウマ娘ゲーム画面限定 リアルタイムアナライズ】**\n\n"
            "1. 🎯 **レース種別 ＆ 結果**: 【育成中重賞・皐月賞 (GI / 中山 芝2000m)】 **2着**\n"
            "   (他出走: 5着 クロノジェネシス / 6着 トウカイテイオー / 7着 フルートリズム)\n\n"
            "2. 🔍 **レース展開 ＆ 勝因・敗因アナライズ**:\n"
            "   ・中盤ポジキ争いおよび第3〜4コーナーでの外目進出の位置取りが勝敗の分岐点です。\n"
            "   ・終盤コーナーでの最速加速固有（ニシノ固有『つぼみ』等）の発動タイミングと最終直線での馬群ブロック回避が1着との勝敗を分けました。\n\n"
            "3. 💡 **プロの勝利・育成改善アドバイス**:\n"
            "   ・次走のクラシック最高峰『日本ダービー (2400m)』に向けたスタミナ目標値の確保が必須です。\n"
            "   ・中盤位置取りを制する『先行直線◯/コーナー◯』および最速加速の白因子強化を最優先で補強しましょう！"
        )
        
        file = discord.File(IMAGE_PATH, filename="umamusume_game_only.png")
        await channel.send(
            content=f"📌 **【ウマ娘ゲーム画面100%限定 リアルタイムアナライズ】**\n\n{report_text}",
            file=file
        )
        print("SUCCESS_POST_PURE_UMA_ONLY")
    await client.close()

if TOKEN:
    client.run(TOKEN)
