import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1536523629708451941
IMAGE_PATH = r"C:\Users\`ken\.gemini\antigravity\brain\0bec0171-9827-45ca-8d9c-40d2ac3ccf5d\.user_uploaded\media_1786407923904.png"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} for instant posting...")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("Searching channel by name...")
        for guild in client.guilds:
            for ch in guild.text_channels:
                if "ルームマッチ" in ch.name or "分析" in ch.name:
                    channel = ch
                    break

    if channel:
        with open("ai_result.txt", "r", encoding="utf-8") as f:
            report_text = f.read()
        
        file = discord.File(IMAGE_PATH, filename="satukisho_result.png")
        await channel.send(
            content=f"🏁 **【全自動レース完了検知 ＆ リアルタイムプロアナライズ】**\n"
                    f"レース終了画面を全自動キャプチャし、勝因・敗因・物理展開を分析いたしました！\n\n"
                    f"{report_text}",
            file=file
        )
        print("✅ SUCCESS! Posted instant report to Discord channel!")
    else:
        print("❌ Could not find target channel.")
    
    await client.close()

if TOKEN:
    client.run(TOKEN)
