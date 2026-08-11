import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

log_path = os.path.join(os.path.dirname(__file__), "on_message_debug.log")

@client.event
async def on_ready():
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] Debug bot ready as {client.user}\n")
    print(f"Debug bot logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    import datetime
    log_line = f"[{datetime.datetime.now()}] MSG: author={message.author}, ch={message.channel.id}({message.channel.name if hasattr(message.channel, 'name') else ''}), content='{message.content}'\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)
    print(log_line.strip())

if __name__ == "__main__":
    import datetime
    if TOKEN:
        client.run(TOKEN)
