import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

async def ensure_usage_pin(client: discord.Client):
    """チャンネルのトップピンに使用ガイドを作成/更新する"""
    channel = client.get_channel(1396001392581148764)
    if not channel:
        print("Usage channel not found")
        return
    # 既存のピンを取得し、同じタイトルのものがあれば更新
    try:
        pins = await channel.pins()
    except Exception as e:
        print(f"Error fetching pins: {e}")
        pins = []
    target_title = "🔰 ウマ娘攻略AIアシスタント 使い方ガイド"
    embed = discord.Embed(
        title=target_title,
        description="このBotは、YouTubeの最新ウマ娘攻略動画（チャンミ・LOHなど）を自動で学習し、あなたの質問に答える専用AIです！",
        color=discord.Color.blue()
    )
    embed.add_field(name="💬 質問する", value="**`/uma [質問内容]`**\n例：逃げウマ娘の育成論を教えて、今の環境で強いサポカは？など、なんでも聞いてください！", inline=False)
    embed.add_field(name="📚 学習済みデータを見る", value="**`/umaknowledge`**\nAIが現在覚えている攻略動画の一覧を自分だけに表示します（ボタンで即消去可能）。", inline=False)
    embed.add_field(name="📥 動画/再生リストを学習させる", value="**`/umalearn [URL]`**\nYouTubeの動画や再生リストのURLを貼り付けて、AIに手動学習させます。", inline=False)
    embed.add_field(name="🌐 攻略Webサイトを登録する", value="**`/umaweblearn [URL]`**\n『ウマ娘.攻略.tools』などの神サイト・ブログのURLを登録し、優先的に深掘り参照させます。", inline=False)
    embed.add_field(name="⚙️ 通知を設定する", value="**`/umasetting`**\nBotが新しい動画を学習した際、スマホにプッシュ通知(メンション)を送るかを設定できます。各自でオン/オフの切り替えが可能です。", inline=False)
    embed.add_field(name="🔄 Botを再起動する (管理者限定)", value="**`/umarestart`**\nBotのプログラムを最新状態に自動再起動します（持ち主のみ実行可能）。", inline=False)
    embed.add_field(name="⏰ 自動学習スケジュール", value="毎日 **06:00 / 12:00 / 16:15 / 22:00** 頃（＋2時間ごとの暇な待機時間）に新着動画を自動チェックします。", inline=False)
    embed.set_footer(text="いつでも最新の攻略情報を引き出せます！どんどん活用してくださいね！")
    # 既にピンされている場合は内容更新、無ければ新規送信してピン留め
    for m in pins:
        if m.author == client.user and m.embeds and m.embeds[0].title == target_title:
            try:
                await m.edit(embed=embed)
                print("Usage pin updated")
                return
            except Exception as e:
                print(f"Error editing usage pin: {e}")
    # 作成してピン留め
    try:
        msg = await channel.send(embed=embed)
        await msg.pin()
        print("Usage pin created and pinned")
    except Exception as e:
        print(f"Error creating usage pin: {e}")

class UsageBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await ensure_usage_pin(self)
        await self.close()

if __name__ == "__main__":
    client = UsageBot()
    client.run(TOKEN)
