import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"✅ Bot is ALIVE and ONLINE as {client.user}")
    ch = client.get_channel(1536523629708451941)
    if ch:
        await ch.send("🟢 **【UmAI Bot 復帰完了】**\nシステムが100%正常起動いたしました！コマンドおよび全自動分析が利用可能です！")
    await client.close()

client.run(token)
