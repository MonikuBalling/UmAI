import os
import sys

# プロジェクトルートディレクトリをPythonパスに追加
project_root = r"c:\Users\`ken\OneDrive\Desktop\UMAMUSUME便利アプリ開発用Project\YOUTUBE_AI"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(project_root, ".env"))

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in for guide refresh as {client.user}")
    from bot_helpers import refresh_channel_guides_and_pins
    await refresh_channel_guides_and_pins(client)
    print("Guide refresh task completed. Closing...")
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
