import asyncio
import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class OneTimeBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def setup_hook(self):
        self.loop.create_task(self.post_and_exit())

    async def post_and_exit(self):
        await self.wait_until_ready()
        channel = self.get_channel(1396001392581148764)
        
        # Unpin old
        pinned_messages = await channel.pins()
        for m in pinned_messages:
            if m.author == self.user and m.embeds and "おはようございます！" in str(m.embeds[0].title):
                await m.unpin()
                
        # Send new
        embed = discord.Embed(
            title="☀️ おはようございます！",
            description="本日のウマ娘AI 最新動画の巡回（学習）スケジュールをお知らせします！",
            color=discord.Color.orange()
        )
        schedule_text = (
            "・第1回： **12:00 頃**\n"
            "・第2回： **16:15 頃** ✨(※YouTubeAPI制限リセット直後！新着入りやすいです)\n"
            "・第3回： **22:00 頃**\n"
            "・第4回： **翌朝 06:00 頃**\n"
        )
        embed.add_field(name="【本日の自動巡回スケジュール】", value=schedule_text, inline=False)
        embed.set_footer(text="今日も1日、良い育成ができますように！")
        
        msg = await channel.send(embed=embed)
        await msg.pin()
        print("Successfully posted and pinned!")
        await self.close()

bot = OneTimeBot()
bot.run(TOKEN)
