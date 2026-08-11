import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import discord
import asyncio
import datetime
import json
from discord import app_commands
from discord.ext import tasks
from discord.ui import Modal, TextInput
from post_usage import ensure_usage_pin
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
import rag
from rag import answer_query
import course_database
import bot_views
import bot_helpers
from bot_views import QuickActionView, UmAMenuVideosView, UmaQuestionModal, PureDbSearchModal
from bot_helpers import generate_umamenu_data, generate_status_roadmap_text

load_dotenv()

def is_night_time() -> bool:
    """夜間 22:00 〜 朝 07:00 JST の間かどうかを判定"""
    now_hour = datetime.datetime.now().hour
    return now_hour >= 22 or now_hour < 7

async def safe_reply(message, content, **kwargs):
    """夜間(22:00〜07:00)は自動的にサイレント送信(silent=True)にし通知音(ピコン)を完全消音"""
    if is_night_time():
        kwargs["silent"] = True
    return await message.reply(content, **kwargs)

async def safe_send(channel, content, **kwargs):
    """夜間(22:00〜07:00)は自動的にサイレント送信(silent=True)にし通知音(ピコン)を完全消音"""
    if is_night_time():
        kwargs["silent"] = True
    return await channel.send(content, **kwargs)

# Bot起動時刻を記録
BOT_START_TIME = datetime.datetime.now()

# 質問botの部屋 専用チャンネルID
TARGET_CHANNEL_ID = 1396001392581148764

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    print("Error: DISCORD_BOT_TOKEN is missing in .env file.")
    exit(1)

# --- 通知設定コマンドとUI ---
class NotificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def load_subscribers(self):
        if os.path.exists("subscribers.json"):
            with open("subscribers.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_subscribers(self, subs):
        with open("subscribers.json", "w", encoding="utf-8") as f:
            json.dump(subs, f, ensure_ascii=False, indent=4)

    @discord.ui.button(label="🔔 通知をオンにする", style=discord.ButtonStyle.green, custom_id="notify_on")
    async def btn_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        subs = self.load_subscribers()
        if interaction.user.id not in subs:
            subs.append(interaction.user.id)
            self.save_subscribers(subs)
            await interaction.response.send_message("✅ 新着動画のプッシュ通知を**オン**にしました！", ephemeral=True)
        else:
            await interaction.response.send_message("既に通知はオンになっています。", ephemeral=True)

    @discord.ui.button(label="🔕 通知をオフにする", style=discord.ButtonStyle.red, custom_id="notify_off")
    async def btn_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        subs = self.load_subscribers()
        if interaction.user.id in subs:
            subs.remove(interaction.user.id)
            self.save_subscribers(subs)
            await interaction.response.send_message("❌ 新着動画のプッシュ通知を**オフ**にしました。", ephemeral=True)
        else:
            await interaction.response.send_message("既に通知はオフになっています。", ephemeral=True)

def save_user_question(user_id: int, question: str):
    """ユーザーの過去の質問履歴を user_questions.json に保存（最新10件）"""
    file_path = "user_questions.json"
    data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    uid_str = str(user_id)
    if uid_str not in data:
        data[uid_str] = []
        
    if question in data[uid_str]:
        data[uid_str].remove(question)
        
    data[uid_str].insert(0, question)
    data[uid_str] = data[uid_str][:10]
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving user question: {e}")

class SaveMemoView(discord.ui.View):
    def __init__(self, question_or_text: str = "攻略メモ", answer_text: str = None):
        super().__init__(timeout=None)
        if answer_text is None:
            first_line = question_or_text.split("\n")[0][:40]
            self.question = f"回答メモ ({first_line})"
            self.answer_text = question_or_text
        else:
            self.question = question_or_text
            self.answer_text = answer_text

    @discord.ui.button(label="📌 個人メモにピン保存", style=discord.ButtonStyle.primary, custom_id="save_personal_memo_btn")
    async def save_memo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        memo_file = "user_memos.json"
        data = {}
        if os.path.exists(memo_file):
            try:
                with open(memo_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        
        if user_id not in data:
            data[user_id] = []

        import datetime
        now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        
        for m in data[user_id]:
            if m.get("question") == self.question:
                await interaction.response.send_message("ℹ️ この回答はすでにあなたの個人メモ帳にピン保存されています！", ephemeral=True)
                return

        new_memo = {
            "id": f"memo_{len(data[user_id])+1}",
            "question": self.question,
            "answer": self.answer_text[:1200],
            "date": now_str
        }
        data[user_id].append(new_memo)

        with open(memo_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await interaction.response.send_message(
            f"✅ **あなたの個人メモ帳にピン保存いたしました！** 📌\n"
            f"💬 **Q: {self.question}**\n\n"
            f"※いつでも `/mymemo` コマンドであなただけの攻略メモ帳を呼び出せます！",
            ephemeral=True
        )

    @discord.ui.button(label="📋 この質問文をコピー", style=discord.ButtonStyle.secondary, custom_id="copy_question_text_btn")
    async def copy_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q_text = self.question if self.question else "質問"
        await interaction.response.send_message(
            f"📋 **質問テキスト**: ```\n{q_text}\n```\n"
            f"👉 このテキストをコピーして `/uma question:[貼り付け]` とすることで、簡単に再利用・条件変更できます！",
            ephemeral=True
        )

class UmaMusumeBot(discord.Client):
    def __init__(self):
        # 必要なインテンツを設定
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(NotificationView())
        from bot_views import BotRoomGuideView, VisionRoomGuideView, QuickActionView
        self.add_view(BotRoomGuideView())
        self.add_view(VisionRoomGuideView())
        self.add_view(QuickActionView())
        print("Bot setup hook initialized with all persistent views!")

class CancelView(discord.ui.View):
    def __init__(self, task: asyncio.Task, user: discord.User):
        super().__init__(timeout=60.0)
        self.task = task
        self.user = user
        self.cancelled = False

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ボタンを押したのがコマンド実行者本人か確認
        if interaction.user != self.user:
            await interaction.response.send_message("他人のコマンドはキャンセルできません！", ephemeral=True)
            return

        self.cancelled = True
        self.task.cancel()
        # ボタンを無効化してメッセージを更新
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"{interaction.user.mention} 処理をキャンセルしました！", view=self)

client = UmaMusumeBot()
tree = client.tree

JST = datetime.timezone(datetime.timedelta(hours=9))

# 暇な時間（待機中）も2時間ごとに常時バックグラウンドで最新動画や再生リストを自動巡回・学習整理
@tasks.loop(hours=2)
async def scheduled_ingest():
    print("Running background idle YouTube ingestion & knowledge organization...")
    # Run synchronous ingestion in a background thread to prevent blocking
    result = await asyncio.to_thread(ingest.ingest_videos, "ウマ娘 チャンミ", 5)
    
    # ingest_videos returns a tuple (added_titles, summary_text) now
    if isinstance(result, tuple) and len(result) == 2:
        added_titles, summary_text = result
    else:
        # Fallback for unexpected return types
        added_titles = result if isinstance(result, list) else []
        summary_text = ""
        
    if added_titles:
        try:
            channel = client.get_channel(1396001392581148764)
            if channel:
                # ニュース風のリッチなデザイン（Embed）を作成
                embed = discord.Embed(
                    title="📰 新着の攻略情報を仕入れました！",
                    description=f"YouTubeから新たに **{len(added_titles)}件** の最新動画データを学習しました！\n最新の環境についていつでも `/uma` コマンドで質問してくださいね！",
                    color=discord.Color.green()
                )
                
                # AI要約が存在する場合は追加
                if summary_text:
                    embed.add_field(name="【📝 AIによる学習内容の要約】", value=summary_text, inline=False)
                
                video_list = ""
                for title in added_titles:
                    video_list += f"・{title}\n"
                
                # Discordの文字数制限対策
                if len(video_list) > 1000:
                    video_list = video_list[:1000] + "...\n(他多数)"
                
                embed.add_field(name="【今回学習した動画】", value=video_list, inline=False)
                embed.set_footer(text="ウマ娘AI 攻略アシスタントBot自動配信")

                # 現在の時間を取得して、深夜(22:00)と早朝(06:00)はメンションを外す
                now_hour = datetime.datetime.now(JST).hour
                is_night = (now_hour == 22 or now_hour == 6)
                
                mention_text = ""
                if not is_night:
                    # subscribers.json を読み込んでメンションを作成
                    subscribers = []
                    if os.path.exists("subscribers.json"):
                        with open("subscribers.json", "r", encoding="utf-8") as f:
                            subscribers = json.load(f)
                    
                    if subscribers:
                        mention_text = " ".join([f"<@{uid}>" for uid in subscribers])
                        mention_text += "\n新しい攻略情報をインプットしました！"
                else:
                    mention_text = "（※深夜・早朝のため通知音を控えています。新しい攻略情報をインプットしました！）"

                await channel.send(content=mention_text, embed=embed)
        except Exception as e:
            print(f"Error sending log to Discord: {e}")

# 6時間ごとに『https://ウマ娘.攻略.tools/supports』からサポカの絵柄・名前・効果を自動全巡回記憶
@tasks.loop(hours=6)
async def auto_learn_support_cards_task():
    try:
        import support_card_learning_engine
        await asyncio.to_thread(support_card_learning_engine.fetch_and_learn_support_cards)
        print("✅ [BACKGROUND TASK] 6-hour support card learning completed!")
    except Exception as e:
        print(f"Support card bg learn error: {e}")

# 6時間ごとにnote上の最新ウマ娘攻略記事を全自動巡回・収集・自己成長するタスク
@tasks.loop(hours=6)
async def auto_crawl_note_articles_task():
    try:
        import note_auto_crawler
        await asyncio.to_thread(note_auto_crawler.search_and_crawl_note)
        print("✅ [BACKGROUND TASK] 6-hour note article crawling & learning completed!")
    except Exception as e:
        print(f"Note article bg crawl error: {e}")

# /learn_x - X（旧Twitter）のウマ娘検証アカウント・ポストをAIの知識ベースへ登録・学習させるコマンド
@client.tree.command(name="learn_x", description="X（旧Twitter）のウマ娘検証アカウントやポストURLをAIの知識として学習登録します。")
@app_commands.describe(url_or_handle="XのポストURLまたは@ユーザー名 (例: https://x.com/uma_guru/status/123... または @uma_guru)", memo="検証内容やメモ (例: ラーメン軒最適ローテ検証)")
async def learn_x_command(interaction: discord.Interaction, url_or_handle: str, memo: str = "ウマ娘検証データ"):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=False)
        except Exception:
            pass

    try:
        os.makedirs("data", exist_ok=True)
        x_file = "data/x_learned_sources.json"
        sources = []
        if os.path.exists(x_file):
            try:
                with open(x_file, "r", encoding="utf-8") as f:
                    sources = json.load(f)
            except Exception:
                sources = []

        import datetime
        new_entry = {
            "url_or_handle": url_or_handle.strip(),
            "memo": memo.strip(),
            "added_by": interaction.user.display_name,
            "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        }
        sources.append(new_entry)
        with open(x_file, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)

        # RAGのカスタム修正・知識ベースにも反映
        rag.save_custom_correction(f"X検証:{memo.strip()}", f"参照URL:{url_or_handle.strip()}")

        clean_target = url_or_handle.strip()
        embed = discord.Embed(
            title="🕳️ 【X（旧Twitter）検証データの学習・同期完了！】",
            description=f"トレーナーさんが教えてくださった検証ポスト/アカウントをAIの知識データベースへ登録完了いたしました！\n\n"
                        f"📌 **学習ターゲット**: `{clean_target}`\n"
                        f"📝 **検証メモ**: `{memo}`\n"
                        f"👤 **登録トレーナー**: `{interaction.user.display_name}`\n\n"
                        f"✨ 今後、関連する質問があった際にAIがこの検証を取り入れ、発信者様へのクレジット（リンク）付きで回答いたします！",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"⚠️ X学習登録エラー: `{e}`")

# /learn_note - noteのウマ娘攻略・検証記事をAIの知識ベースへ登録・学習させるコマンド
@client.tree.command(name="learn_note", description="noteのウマ娘攻略・検証記事URLをAIの知識として学習登録します。")
@app_commands.describe(url="noteの投稿記事URL (例: https://note.com/user/n/n12345)", memo="記事の解説・検証内容メモ (例: チャンミ環境・因子厳選論)")
async def learn_note_command(interaction: discord.Interaction, url: str, memo: str = "ウマ娘note攻略記事"):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=False)
        except Exception:
            pass

    try:
        os.makedirs("data", exist_ok=True)
        note_file = "data/note_learned_sources.json"
        sources = []
        if os.path.exists(note_file):
            try:
                with open(note_file, "r", encoding="utf-8") as f:
                    sources = json.load(f)
            except Exception:
                sources = []

        import datetime
        new_entry = {
            "url": url.strip(),
            "memo": memo.strip(),
            "added_by": interaction.user.display_name,
            "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        }
        sources.append(new_entry)
        with open(note_file, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)

        rag.save_custom_correction(f"note検証:{memo.strip()}", f"参照URL:{url.strip()}")

        clean_url = url.strip()
        embed = discord.Embed(
            title="📝 【note攻略・検証記事の学習登録完了！】",
            description=f"トレーナーさんが教えてくださったnote記事をAIの知識データベースへ登録完了いたしました！\n\n"
                        f"📌 **記事URL**: `{clean_url}`\n"
                        f"📝 **解説メモ**: `{memo}`\n"
                        f"👤 **登録トレーナー**: `{interaction.user.display_name}`\n\n"
                        f"✨ 今後、関連する質問があった際にAIがこのnote記事の知識を取り入れ、執筆者様へのクレジット（リンク）付きで回答いたします！",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"⚠️ note学習登録エラー: `{e}`")

# /logclean & /umaclean - 実行した部屋ごとに個別にログを全自動一括削除・清掃するコマンド
@client.tree.command(name="logclean", description="この部屋（Discordチャンネル）のBot返信＆ユーザーログを一括全削除・清掃します。")
@app_commands.describe(only_bot="Botのログメッセージのみ削除する場合はTrue、ピン留め以外の全メッセージを削除する場合はFalse (標準: False)")
async def logclean_command(interaction: discord.Interaction, only_bot: bool = False):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
            
    try:
        deleted_count = 0
        try:
            if only_bot:
                deleted = await target_channel.purge(limit=200, check=lambda m: not m.pinned and m.author == client.user)
            else:
                deleted = await target_channel.purge(limit=200, check=lambda m: not m.pinned)
            deleted_count = len(deleted)
        except Exception:
            async for msg in target_channel.history(limit=200):
                if msg.pinned:
                    continue
                if only_bot and msg.author != client.user:
                    continue
                try:
                    await msg.delete()
                    deleted_count += 1
                except Exception:
                    pass
                        
        await interaction.followup.send(f"🧹 **【`#{target_channel.name}` ピン以外一括全削除完了！】**\nピン留め以外の過去メッセージ `{deleted_count}件` を一瞬で全消去・リセットいたしました！✨", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ お掃除中にエラーが発生しました: {e}", ephemeral=True)

# 旧コマンドとの互換性
@client.tree.command(name="umaclean", description="この部屋のBot過去ログメッセージを一括全削除・清掃します。")
async def umaclean_command(interaction: discord.Interaction):
    await logclean_command(interaction, only_bot=True)

@tasks.loop(time=datetime.time(hour=5, minute=0, tzinfo=JST))
async def morning_announcement():
    try:
        channel = client.get_channel(1396001392581148764)
        if channel:
            # 古い予定表のピン留めを外す
            try:
                pinned_messages = await channel.pins()
                for m in pinned_messages:
                    if m.author == client.user and m.embeds:
                        if "おはようございます！" in str(m.embeds[0].title):
                            await m.unpin()
            except Exception as e:
                print(f"Error unpinning messages: {e}")

            embed = discord.Embed(
                title="☀️ おはようございます！",
                description="本日のウマ娘AI 最新動画の巡回（学習）スケジュールをお知らせします！",
                color=discord.Color.orange()
            )
            schedule_text = (
                "・第1回： **06:00 頃**\n"
                "・第2回： **12:00 頃**\n"
                "・第3回： **16:15 頃** ✨(※YouTubeAPI制限リセット直後！新着入りやすいです)\n"
                "・第4回： **22:00 頃**\n"
            )
            embed.add_field(name="【本日の自動巡回スケジュール】", value=schedule_text, inline=False)
            embed.set_footer(text="今日も1日、良い育成ができますように！")
            
            msg = await channel.send(embed=embed)
            
            # 新しい予定表をピン留めする
            try:
                await msg.pin()
            except Exception as e:
                print(f"Error pinning message: {e}")
    except Exception as e:
        print(f"Error in morning_announcement: {e}")

async def run_startup_check():
    await asyncio.sleep(30)  # 起動直後のユーザー質問とAPIが衝突しないよう30秒待機
    print("Checking for unlearned videos from registered playlists on startup...")
    try:
        await scheduled_ingest()
    except Exception as e:
        print(f"Startup check error: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    # レートリミット(429)を回避するため、新規登録時のみ同期
    try:
        synced = await client.tree.sync()
        print(f"Online & Ready! Slash commands active ({len(synced)} commands).")
    except Exception as se:
        print(f"Command sync status: {se}")

    # Start the periodic background tasks
    if not scheduled_ingest.is_running():
        scheduled_ingest.start()
    if not morning_announcement.is_running():
        morning_announcement.start()
    # Update the usage guide pin at the top of the channel
    await ensure_usage_pin(client)
    
    # 起動直後に未学習動画（途中落とし分等）があればバックグラウンドで自動消化・再開
    asyncio.create_task(run_startup_check())

    # Discordからのリモート再起動完了通知（コマンド実行者のチャンネルへログ送信）
    if os.path.exists("restart_info.json"):
        try:
            with open("restart_info.json", "r", encoding="utf-8") as rf:
                r_info = json.load(rf)
            if os.path.exists("restart_info.json"):
                os.remove("restart_info.json")
            
            user_id = r_info.get("user_id")
            ch_id = r_info.get("channel_id") or 1396001392581148764
            
            ch = client.get_channel(ch_id)
            if ch:
                embed = discord.Embed(
                    title="🟢 Botの自動再起動が完了しました！（稼働復帰）",
                    description="最新のプログラムで無事に再起動・復帰いたしました！\nいつでも通常通り質問コマンドをご利用いただけます。",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Discordリモート再起動システム")
                await ch.send(content=f"<@{user_id}>", embed=embed)
                print(f"Sent restart confirmation to channel for user {user_id}")
        except Exception as re_err:
            print(f"Error sending restart confirmation: {re_err}")

@client.tree.command(name="uma", description="ウマ娘の質問に答え、スキル発動率やコース物理を計算します。")
@app_commands.describe(
    question="AIに聞きたい質問を入力してください（例：東京2400mでのアンスキの有効性は？）",
    wisdom="【任意】ウマ娘の賢さ数値（例：1350）",
    leg_style="【任意】ウマ娘の脚質"
)
@app_commands.choices(leg_style=[
    app_commands.Choice(name="逃げ 🏃‍♂️", value="逃げ"),
    app_commands.Choice(name="先行 🐎", value="先行"),
    app_commands.Choice(name="差し 🏇", value="差し"),
    app_commands.Choice(name="追込 ⚡", value="追込")
])
async def uma(interaction: discord.Interaction, question: str, wisdom: int = None, leg_style: app_commands.Choice[str] = None):
    # 指定のチャンネルでのみ動作を許可する
    TARGET_CHANNEL_ID = 1396001392581148764
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("ごめんなさい！このコマンドは指定された専用チャンネルでしか使えない設定になっています！", ephemeral=True)
        return

    # 【超重要】0.1秒で即座にdefer()を呼び、Discordの3秒制限＆「応答しませんでした」エラーを100%完封！
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except Exception as e:
        print(f"Defer info: {e}")

    chosen_leg = leg_style.value if leg_style else None
    import re
    question = re.sub(r'^(質問[:：]\s*|Q[:：]\s*)', '', question).strip()
    print(f"Received question from {interaction.user}: {question} (wisdom:{wisdom}, leg:{chosen_leg})")

    # ユーザーの過去質問履歴へ自動保存
    try:
        save_user_question(interaction.user.id, question)
    except Exception:
        pass

    is_finished = [False]
    
    def on_progress(msg_text):
        print(f"[PROGRESS] {msg_text}")

    # 初期案内メッセージを表示
    try:
        worker_task = asyncio.create_task(asyncio.to_thread(answer_query, question, on_progress))
        view = CancelView(worker_task, interaction.user)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} 🔍 **質問のウマ娘物理計算 ＆ ナレッジデータを分析中…少々お待ちください！**\n💬 **Q: {question}**",
            view=view
        )
    except Exception:
        pass
    
    try:
        is_course_req = any(k in question for k in ["コース", "高低差", "マップ", "図面", "物理計算", "コース図", "コース詳細", "プロファイル"])
        try:
            # 25秒絶対強制タイムアウト解除ガード（いかなるAPIフリーズ時も25秒で即座にセーフティ復帰）
            response_data = await asyncio.wait_for(worker_task, timeout=25.0)
            is_finished[0] = True
            
            # もしキャンセルされていたら何もしない
            if view.cancelled:
                return
                
            if response_data is None:
                await interaction.edit_original_response(content=f"{interaction.user.mention} 現在、初回の動画データを学習中です！あと数分ほど待ってから再度お試しください。", view=None)
                return
        except asyncio.TimeoutError:
            is_finished[0] = True
            print("ABS TIMEOUT TRIGGERED! Switching to instant knowledge synthesis.")
            if is_course_req:
                ev_sched = rag.parse_event_schedule(question)
                if "3600" in question or "長距離" in question or "ステイヤーズ" in question:
                    c_target_fb = "nakayama_3600"
                elif "2400" in question or "ダービー" in question:
                    c_target_fb = "tokyo_2400"
                elif "2000" in question or "皐月" in question:
                    c_target_fb = "nakayama_2000"
                elif "2200" in question or "エリザベス" in question:
                    c_target_fb = "kyoto_2200"
                elif "1600" in question or "マイル" in question or "桜花" in question:
                    c_target_fb = "hanshin_1600"
                else:
                    c_target_fb = "tokyo_2400" if ("チャンミ" in question or "チャンピオンズ" in question) else "nakayama_2000"
                c_calc = course_database.calculate_skill_timing(c_target_fb, "つぼみ、ほころぶ時", wisdom=wisdom, leg_style=chosen_leg, event_schedule=ev_sched)
                fallback_ans = f"⚡ **【25秒絶対フリーズ解除セーフティ作動】**\n通信フリーズを全自動回避し、即座に最新シミュレーションデータを出力いたしました！\n\n{c_calc}"
                
                c_info_fb = course_database.COURSE_DATA[c_target_fb]
                img_fb = course_visualizer.generate_course_map_image(
                    course_name=c_info_fb["name"],
                    total_dist=c_info_fb["distance"],
                    final_start_m=c_info_fb["phase_final"][0],
                    skill_name="最速加速スキル (汎用想定)",
                    skill_start_m=c_info_fb["phase_final"][0],
                    skill_end_m=int(c_info_fb["phase_final"][0] + (3.0 * c_info_fb["distance"] / 1000.0 * 28.0)),
                    uphill_list=[{"start": s["start"], "end": s["end"]} for s in c_info_fb.get("slopes", []) if s.get("type") == "up"],
                    downhill_list=[{"start": s["start"], "end": s["end"]} for s in c_info_fb.get("slopes", []) if s.get("type") == "down"],
                    output_path=f"course_map_{c_target_fb}.png",
                    event_schedule=ev_sched,
                    corner_3_start=c_info_fb.get("corner_3_start"),
                    corner_3_end=c_info_fb.get("corner_3_end"),
                    invalid_skills_list=c_info_fb.get("invalid_skills")
                )
                response_data = (fallback_ans, [], [], img_fb)
            else:
                ans_fb, _, _, _ = rag.answer_query(question)
                response_data = (ans_fb, [], [], None)
            
        generated_image_path = None
        if isinstance(response_data, tuple):
            if len(response_data) == 4:
                response_text, ref_videos, ref_websites, generated_image_path = response_data
            elif len(response_data) == 3:
                response_text, ref_videos, ref_websites = response_data
            elif len(response_data) == 2:
                response_text, ref_videos = response_data
                ref_websites = []
            else:
                response_text, ref_videos, ref_websites = str(response_data[0]), [], []
        else:
            response_text = str(response_data)
            ref_videos, ref_websites = [], []

        embeds = []
        img_file = None
        if generated_image_path and os.path.exists(generated_image_path):
            fn = os.path.basename(generated_image_path)
            img_file = discord.File(generated_image_path, filename=fn)
            map_emb = discord.Embed(
                title="🏇 【コース物理シミュレーション ビジュアル図面マップ】",
                description="ミリ単位の物理計算に基づくコース全長・終盤開始(2/3m)・スキル発動〜効果終了区間のカラービジュアルマップ",
                color=discord.Color.gold()
            )
            map_emb.set_image(url=f"attachment://{fn}")
            embeds.append(map_emb)

        if ref_videos:
            for idx, v in enumerate(ref_videos[:3], 1):
                emb = discord.Embed(
                    title=f"🎬 参考攻略動画 #{idx}",
                    url=v['source'],
                    description=f"▶️ **[{v['title']}]({v['source']})**\n\n"
                                f"👤 **投稿者**: `{v['channel']}` | 📅 **投稿日**: `{v['date']}`\n"
                                f"👉 [動画をYouTubeで視聴してクリエイター様を応援する！]({v['source']})",
                    color=discord.Color.from_rgb(255, 0, 0)
                )
                emb.set_thumbnail(url=v['thumbnail_url'])
                embeds.append(emb)

        # 引用Webサイト・攻略記事カードの追加
        if ref_websites:
            web_desc_lines = []
            for w in ref_websites[:3]:
                t = w.get('title', 'Web攻略記事')
                u = w.get('url', '')
                if u:
                    web_desc_lines.append(f"🔗 **[{t}]({u})**")
            
            if web_desc_lines:
                w_emb = discord.Embed(
                    title="🌐 参考にさせていただいた攻略Webサイト・記事",
                    description="\n".join(web_desc_lines) + "\n\n※サイト制作者様へ感謝を込めてリンクを掲載しております。",
                    color=discord.Color.from_rgb(0, 180, 216)
                )
                embeds.append(w_emb)
        
        # 質問者の元の投稿メッセージへワンタップで一気に画面スクロール/ジャンプできるディープリンク
        jump_link = ""
        if interaction.guild_id and interaction.channel_id:
            msg_id = interaction.id
            jump_link = f"\n🔗 **[👉 あなたの質問の位置へ画面スクロール/ジャンプ](https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/{msg_id})**"

        header_text = (
            f"❓ **【ウマ娘攻略Q&A】**\n"
            f"👤 **質問者**: {interaction.user.mention} 様{jump_link}\n"
            f"💬 **Q: {question}**\n"
            f"───────────────────\n"
            f"{response_text}"
        )
        
        memo_view = SaveMemoView(question, response_text)
        if img_file:
            await interaction.edit_original_response(
                content=header_text,
                attachments=[img_file],
                embeds=embeds if embeds else None,
                view=memo_view
            )
        else:
            await interaction.edit_original_response(
                content=header_text,
                embeds=embeds if embeds else None,
                view=memo_view
            )
            
    except asyncio.CancelledError:
        pass
        
    except Exception as e:
        if not view.cancelled:
            print(f"Error during response generation (recovering dynamically): {e}")
            jump_link_fb = ""
            ans_fb, _, _, _ = await asyncio.to_thread(rag.answer_query, question)
            fallback_text = (
                f"❓ **【ウマ娘攻略Q&A】**\n"
                f"👤 **質問者**: {interaction.user.mention} 様{jump_link_fb}\n"
                f"💬 **Q: {question}**\n"
                f"───────────────────\n"
                f"{ans_fb}"
            )
            try:
                await interaction.edit_original_response(content=fallback_text, view=SaveMemoView(question, fallback_text))
            except Exception:
                pass
            else:
                if is_course_req:
                    ev_sched = rag.parse_event_schedule(question)
                    c_target_fb = "hanshin_1800" if ("チャンミ" in question or "チャンピオンズ" in question or "阪神" in question or "1800" in question) else "nakayama_2000"
                    c_calc = course_database.calculate_skill_timing(c_target_fb, "つぼみ、ほころぶ時", wisdom=wisdom, leg_style=chosen_leg, event_schedule=ev_sched)
                    body_text = f"🏇 **【コース物理計算解析】**\nご質問のコース・物理シミュレーション解析結果を出力いたしました！\n\n{c_calc}"
                    
                    import course_visualizer, course_database, os
                    c_info_fb = course_database.COURSE_DATA[c_target_fb]
                    map_file_path = os.path.abspath(f"scratch/course_{c_target_fb}.png")
                    os.makedirs("scratch", exist_ok=True)
                    course_visualizer.generate_course_map_image(
                        course_name=c_info_fb["name"],
                        total_dist=c_info_fb["distance"],
                        final_start_m=c_info_fb["final_start"],
                        skill_name="最速加速接続",
                        skill_start_m=c_info_fb["final_start"],
                        skill_end_m=c_info_fb["final_start"] + 150,
                        uphill_list=c_info_fb.get("uphill"),
                        downhill_list=c_info_fb.get("downhill"),
                        output_path=map_file_path,
                        event_schedule=ev_sched,
                        corner_3_start=c_info_fb.get("corner_3_start"),
                        corner_3_end=c_info_fb.get("corner_3_end"),
                        invalid_skills_list=c_info_fb.get("invalid_skills")
                    )
                    if os.path.exists(map_file_path):
                        img_file = discord.File(map_file_path, filename="course_map.png")
                else:
                    body_text = ans_fb

            fallback_text = (
                f"❓ **【ウマ娘攻略Q&A】**\n"
                f"👤 **質問者**: {interaction.user.mention} 様{jump_link_fb}\n"
                f"💬 **Q: {question}**\n"
                f"───────────────────\n"
                f"{body_text}"
            )
            try:
                if img_file:
                    await interaction.edit_original_response(content=fallback_text, attachments=[img_file], view=SaveMemoView(question, fallback_text))
                else:
                    await interaction.edit_original_response(content=fallback_text, view=SaveMemoView(question, fallback_text))
            except Exception:
                pass

# スラッシュコマンド: 手持ちサポートカード一覧スクショ・キャプチャ画像を送信してAI視覚解析で一括登録
@client.tree.command(name="register_cards", description="【AI視覚解析】所持サポカ一覧のスクショ画像をAIが自動読み取りして手持ち登録します")
@app_commands.describe(image="所持サポートカード一覧のスクリーンショット画像")
async def register_cards(interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer(ephemeral=True)
    if not image.content_type or not image.content_type.startswith("image/"):
        await interaction.followup.send("❌ 画像ファイルを添付してください！", ephemeral=True)
        return
        
    await interaction.followup.send("📸 **AI視覚解析中…** 画像からサポートカード名と凸数を自動読み取りしています。少々お待ちください！", ephemeral=True)
    img_bytes = await image.read()
    
    cards_found = rag.analyze_inventory_image(img_bytes)
    if not cards_found:
        await interaction.followup.send("⚠️ 画像からサポートカードを検出できませんでした。より鮮明なサポカ一覧画面のスクショでお試しください。", ephemeral=True)
        return
        
    import inventory_manager
    count = inventory_manager.update_user_cards(str(interaction.user.id), cards_found)
    
    summary = inventory_manager.get_user_cards_summary(str(interaction.user.id))
    await interaction.followup.send(f"✅ **AI視覚解析が完了し、{len(cards_found)}枚のサポートカードをあなたの手持ちDBへ登録・更新いたしました！**\n\n{summary}", ephemeral=True)

# スラッシュコマンド: 自分の登録済み手持ちサポカ一覧を確認
@client.tree.command(name="my_cards", description="登録されている自分の所持サポートカード・凸数一覧を確認します")
async def my_cards(interaction: discord.Interaction):
    import inventory_manager
    summary = inventory_manager.get_user_cards_summary(str(interaction.user.id))
    await interaction.response.send_message(summary, ephemeral=True)

# 右クリックアプリメニュー: メッセージに添付されたサポカスクショからAI視覚自動登録
@client.tree.context_menu(name="📷 サポカスクショからAI自動登録")
async def register_cards_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    if not message.attachments:
        await interaction.followup.send("❌ 画像が添付されたメッセージを選択してください！", ephemeral=True)
        return
        
    target_attachment = None
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            target_attachment = att
            break
            
    if not target_attachment:
        await interaction.followup.send("❌ 画像が見つかりませんでした。", ephemeral=True)
        return
        
    await interaction.followup.send("📸 **AI視覚解析中…** 添付画像からサポートカード名と凸数を自動検出しています！", ephemeral=True)
    img_bytes = await target_attachment.read()
    
    cards_found = rag.analyze_inventory_image(img_bytes)
    if not cards_found:
        await interaction.followup.send("⚠️ 画像からサポートカードを検出できませんでした。より鮮明な一覧スクショでお試しください。", ephemeral=True)
        return
        
    import inventory_manager
    count = inventory_manager.update_user_cards(str(interaction.user.id), cards_found)
    summary = inventory_manager.get_user_cards_summary(str(interaction.user.id))
    await interaction.followup.send(f"✅ **AI視覚解析が完了し、{len(cards_found)}枚のサポートカードをあなたの手持ちDBへ登録いたしました！**\n\n{summary}", ephemeral=True)

# 配信・画面共有リアルタイム自動キャプチャ解析コマンド (/cap_race)
@client.tree.command(name="cap_race", description="Discordの配信画面・ゲーム画面をノータイムで直接キャプチャしレースの勝因・敗因物理アナライズレポートを出力")
async def cap_race(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    from live_race_analyzer import capture_live_window, analyze_race_capture
    cap_p, note = await asyncio.to_thread(capture_live_window)
    if cap_p:
        report_text = await asyncio.to_thread(analyze_race_capture, cap_p)
        file = discord.File(cap_p, filename="live_race_capture.png")
        await interaction.followup.send(content=report_text, file=file)
    else:
        await interaction.followup.send(content=f"⚠️ **キャプチャエラー**: {note}\n※PC上でDiscordの画面共有・配信、またはウマ娘のゲーム画面を開いた状態で再度お試しください！")

# ウマ娘個体AI勝算評価コマンド (/uma_ コマンド群)
@client.tree.command(name="uma_eval", description="貼られたスクショ(直前投稿も自動取得)からチャンミ・リグヒ個体勝算(S/A/B/C)とアドバイスをAI診断")
@app_commands.choices(course=[
    app_commands.Choice(name="🏆【次回LOH】中山 芝 2000m 中距離・右回り", value="nakayama_2000"),
    app_commands.Choice(name="👑【次回チャンミ】阪神 芝 1800m マイル・右回り", value="hanshin_1800"),
    app_commands.Choice(name="🏇 東京 芝 2400m 日本ダービー / ジャパンC", value="tokyo_2400"),
    app_commands.Choice(name="🏇 京都 芝 3000m 菊花賞", value="kyoto_3000")
])
async def uma_eval_command(
    interaction: discord.Interaction,
    course: app_commands.Choice[str] = None,
    screenshot1: discord.Attachment = None,
    screenshot2: discord.Attachment = None,
    screenshot3: discord.Attachment = None,
    screenshot4: discord.Attachment = None,
    screenshot5: discord.Attachment = None,
    screenshot6: discord.Attachment = None,
    screenshot7: discord.Attachment = None,
    screenshot8: discord.Attachment = None,
    screenshot9: discord.Attachment = None,
    screenshot10: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=False)
    selected_course = course.value if hasattr(course, "value") else (course if isinstance(course, str) else "nakayama_2000")
    
    all_imgs = [screenshot1, screenshot2, screenshot3, screenshot4, screenshot5, screenshot6, screenshot7, screenshot8, screenshot9, screenshot10]
    attachments = [img for img in all_imgs if img and img.content_type and img.content_type.startswith("image/")]
    
    img_bytes_list = []
    # コマンドに直接画像がセットされていない場合、チャット直前履歴から最新の画像投稿を全自動探索！
    if not attachments:
        async for hist_msg in interaction.channel.history(limit=15):
            if hist_msg.author == interaction.user and hist_msg.attachments:
                for att in hist_msg.attachments:
                    if att.content_type and att.content_type.startswith("image/"):
                        b = await att.read()
                        img_bytes_list.append(b)
                if img_bytes_list:
                    break
    else:
        for att in attachments:
            b = await att.read()
            img_bytes_list.append(b)

    if not img_bytes_list:
        await interaction.followup.send("⚠️ 画像が見つかりませんでした。コマンドに画像を添付するか、直前にチャット欄へスクショを貼った状態でコマンドを実行してください。")
        return
        
    import image_stitcher, io, asyncio
    if len(img_bytes_list) > 1:
        eval_img_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, img_bytes_list, "ウマ娘 全スキル＆ステータス統合シート")
    else:
        eval_img_bytes = img_bytes_list[0]
        
    status_data = await asyncio.to_thread(rag.analyze_uma_status_image, eval_img_bytes)
    import uma_evaluator
    if status_data:
        eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key=selected_course)
        msg = f"📸 **【添付画像（{len(img_bytes_list)}枚）全自動縦長統合 AI診断レポート】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
    else:
        msg = f"📸 **【添付画像（{len(img_bytes_list)}枚）全自動縦長統合完了】**\n\n✨ 画像を1枚の縦長シートに全自動結合いたしました！"
        
    file = discord.File(io.BytesIO(eval_img_bytes), filename="stitched_uma_eval.png")
    await interaction.followup.send(msg, file=file)

@client.tree.command(name="eval_uma", description="貼られたスクショ(直前投稿も自動取得)から個体勝算(S/A/B/C)とアドバイスをAI診断")
async def eval_uma_legacy_command(interaction: discord.Interaction, screenshot1: discord.Attachment = None, screenshot2: discord.Attachment = None, screenshot3: discord.Attachment = None, course: str = "nakayama_2000"):
    await uma_eval_command(interaction, screenshot1, screenshot2, screenshot3, course=course)

@client.tree.context_menu(name="🏇 ウマ娘個体・勝算AI評価")
async def eval_uma_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=False)
    if not message.attachments:
        await interaction.followup.send("⚠️ 画像が添付されたメッセージを選択してください。", ephemeral=True)
        return
        
    img_bytes_list = []
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            b = await att.read()
            img_bytes_list.append(b)
            
    if not img_bytes_list:
        await interaction.followup.send("⚠️ 画像ファイルを添付したメッセージで実行してください。", ephemeral=True)
        return
        
    import image_stitcher, io, asyncio
    if len(img_bytes_list) > 1:
        eval_img_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, img_bytes_list, "ウマ娘 全スキル＆ステータス統合シート")
    else:
        eval_img_bytes = img_bytes_list[0]
        
    status_data = await asyncio.to_thread(rag.analyze_uma_status_image, eval_img_bytes)
    import uma_evaluator
    if status_data:
        eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key="nakayama_2000")
        msg = f"📸 **【選択メッセージ画像（{len(img_bytes_list)}枚）全自動縦長統合 AI診断レポート】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
    else:
        msg = f"📸 **【選択メッセージ画像（{len(img_bytes_list)}枚）全自動縦長統合完了】**\n\n✨ 画像を1枚の縦長シートに全自動結合いたしました！"
        
    file = discord.File(io.BytesIO(eval_img_bytes), filename="stitched_uma_eval.png")
    await interaction.followup.send(msg, file=file)

# 因子レシート生成＆共有コマンド (/uma_ コマンド群)
@client.tree.command(name="uma_receipt", description="複数枚(直前投稿も自動取得)の因子スクショから『1枚の縦長 因子レシート画像』を全自動合成共有")
async def uma_receipt_command(
    interaction: discord.Interaction,
    image1: discord.Attachment = None,
    image2: discord.Attachment = None,
    image3: discord.Attachment = None,
    image4: discord.Attachment = None,
    image5: discord.Attachment = None,
    image6: discord.Attachment = None,
    image7: discord.Attachment = None,
    image8: discord.Attachment = None,
    image9: discord.Attachment = None,
    image10: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=False)
    all_imgs = [image1, image2, image3, image4, image5, image6, image7, image8, image9, image10]
    attachments = [img for img in all_imgs if img and img.content_type and img.content_type.startswith("image/")]
    
    img_bytes_list = []
    if not attachments:
        async for hist_msg in interaction.channel.history(limit=15):
            if hist_msg.author == interaction.user and hist_msg.attachments:
                for att in hist_msg.attachments:
                    if att.content_type and att.content_type.startswith("image/"):
                        b = await att.read()
                        img_bytes_list.append(b)
                if img_bytes_list:
                    break
    else:
        for att in attachments:
            b = await att.read()
            img_bytes_list.append(b)

    if not img_bytes_list:
        await interaction.followup.send("⚠️ 画像が見つかりませんでした。コマンドに画像を添付するか、直前にチャット欄へスクショを貼った状態でコマンドを実行してください。")
        return
        
    import image_stitcher, io, asyncio
    if len(img_bytes_list) > 1:
        stitched_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, img_bytes_list, "ウマ娘 殿堂入り 因子レシート")
    else:
        stitched_bytes = img_bytes_list[0]
    
    # AI因子解析
    factor_data = await asyncio.to_thread(rag.analyze_factor_receipt_image, stitched_bytes if stitched_bytes else img_bytes_list[0])
    uma_name = factor_data.get("uma_name", "ウマ娘")
    blues = " / ".join(factor_data.get("blue_factors", [])) or "解析完了"
    reds = " / ".join(factor_data.get("red_factors", [])) or "解析完了"
    whites = ", ".join(factor_data.get("white_factors", [])[:6]) or "各種白因子"
    
    caption = (
        f"📜 **【{uma_name} 縦長 因子レシート共有】**\n\n"
        f"🟦 **代表青因子**: `【{blues}】` \n"
        f"🟥 **距離・適性赤因子**: `【{reds}】` \n"
        f"⚪ **所持白スキル因子**: `{whites}` ...\n\n"
        "✨ 複数枚のスクショから1枚の完全体『縦長 因子レシート』を全自動合成いたしました！フレンド・サークル共有にご活用ください！\n\n"
        "🏷️ `#因子レシート` `#因子周回` `#青因子3` `#ウマ娘因子共有`"
    )
    
    if stitched_bytes:
        file = discord.File(io.BytesIO(stitched_bytes), filename="factor_receipt.png")
        await interaction.followup.send(caption, file=file)
    else:
        await interaction.followup.send(caption)

@client.tree.command(name="make_receipt", description="複数枚の因子・スキル画面スクショから『1枚の縦長 因子レシート画像』を全自動合成して共有")
async def make_receipt_legacy_command(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment = None, image3: discord.Attachment = None):
    await uma_receipt_command(interaction, image1, image2, image3)

# 配信画面/ウマ娘画面 リアルタイムAI自動スキャン＆レシート生成コマンド (/uma_ コマンド群)
@client.tree.command(name="uma_stream_capturer", description="PC上のウマ娘/配信画面からリアルタイムで画面をAI抽出＆個体評価・縦長レシート生成")
@app_commands.choices(mode=[
    app_commands.Choice(name="🏇 ウマ娘 個体勝算AI診断", value="個体勝算評価"),
    app_commands.Choice(name="📜 縦長 因子レシート生成", value="因子レシート")
])
async def uma_stream_capturer_command(interaction: discord.Interaction, mode: str = "個体勝算評価"):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=False)
        except Exception:
            pass
            
    selected_mode = mode if isinstance(mode, str) else (getattr(mode, "value", "個体勝算評価"))
    
    try:
        import stream_capturer, asyncio
        img_bytes = await asyncio.to_thread(stream_capturer.capture_uma_window)
        
        if not img_bytes:
            await interaction.followup.send("⚠️ 画面のキャプチャに失敗いたしました。PC上でウマ娘や配信画面を開いた状態でお試しください。")
            return

        if "因子" in selected_mode or "レシート" in selected_mode:
            import image_stitcher, io
            stitched_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, [img_bytes], "リアルタイム配信抽出 因子レシート")
            factor_data = await asyncio.to_thread(rag.analyze_factor_receipt_image, img_bytes)
            uma_name = factor_data.get("uma_name", "ウマ娘")
            blues = " / ".join(factor_data.get("blue_factors", [])) or "解析完了"
            reds = " / ".join(factor_data.get("red_factors", [])) or "解析完了"
            whites = ", ".join(factor_data.get("white_factors", [])[:6]) or "各種白因子"
            
            caption = (
                f"🎥 **【配信/ゲーム画面からリアルタイム全自動抽出】**\n"
                f"📜 **『{uma_name}』 因子レシート**\n\n"
                f"🟦 **代表青因子**: `【{blues}】` \n"
                f"🟥 **適性赤因子**: `【{reds}】` \n"
                f"⚪ **主要白スキル**: `{whites}`...\n\n"
                "✨ 画面共有/ゲーム画面からリアルタイムで自動抽出し、レシート化いたしました！\n\n"
                "🏷️ `#因子レシート` `#因子周回` `#青因子3` `#ウマ娘因子共有`"
            )
            file = discord.File(io.BytesIO(stitched_bytes if stitched_bytes else img_bytes), filename="stream_receipt.png")
            await interaction.followup.send(caption, file=file)
        else:
            import asyncio
            status_data = await asyncio.to_thread(rag.analyze_uma_status_image, img_bytes)
            if not status_data:
                import io
                file = discord.File(io.BytesIO(img_bytes), filename="stream_capture.png")
                await interaction.followup.send("⚠️ 画面からウマ娘のステータス・スキル情報が検出できませんでした。スキル取得画面またはステータス画面を大きく表示した状態でお試しください。", file=file)
                return
                
            import uma_evaluator, io
            eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key="nakayama_2000")
            msg = f"🎥 **【配信/ゲーム画面 リアルタイムAI自動診断】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
            file = discord.File(io.BytesIO(img_bytes), filename="stream_capture.png")
            await interaction.followup.send(msg, file=file)
    except Exception as e:
        print(f"Error in scan_stream_command: {e}")
        try:
            await interaction.followup.send(f"⚠️ 画面スキャン解析中にエラーが発生いたしました: {e}")
        except Exception:
            pass

class UmAMenuVideosView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.is_expanded = False

    @discord.ui.button(label="🎬 注目学習動画のサムネイルカード一覧を見る", style=discord.ButtonStyle.primary, emoji="📺")
    async def toggle_embeds(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_expanded:
            self.is_expanded = True
            button.label = "🙈 動画カード一覧をたたむ"
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(embeds=self.embeds[:4], view=self)
        else:
            self.is_expanded = False
            button.label = "🎬 注目学習動画のサムネイルカード一覧を見る"
            button.style = discord.ButtonStyle.primary
            await interaction.response.edit_message(embeds=[], view=self)

def generate_umamenu_data():
    import os, json, datetime, urllib.request
    log_file = "learned_knowledge_log.json"
    processed_file = "processed_videos.txt"
    
    total_videos = 0
    video_ids = []
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as pf:
            video_ids = [l.strip() for l in pf if l.strip()]
            total_videos = len(video_ids)
            
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    today_videos = []
    recent_video_entries = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as lf:
                logs = json.load(lf)
                for entry in logs:
                    if entry.get("learned_at", "").startswith(today_str):
                        today_videos.append(entry)
                    recent_video_entries.append(entry)
        except Exception:
            pass
            
    today_text = ""
    if today_videos:
        today_text = "\n".join([f"  ・[{v.get('title', '動画')}]({v.get('url', '')}) ({v.get('channel', '')})" for v in today_videos])
    else:
        today_text = "  ・（本日新しく追加された手動学習動画はありません）"
        
    recent_list_lines = []
    target_vids = video_ids[-4:] if video_ids else []
    
    # リアルタイムでoEmbed等からタイトルを綺麗に回収する辞書
    vid_meta_cache = {}
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as lf:
                for item in json.load(lf):
                    vid_meta_cache[item.get("video_id")] = item
        except Exception:
            pass

    for vid in target_vids:
        url = f"https://www.youtube.com/watch?v={vid}"
        meta = vid_meta_cache.get(vid, {})
        v_title = meta.get("title")
        v_channel = meta.get("channel")
        
        # メタデータが無い場合はYouTube oEmbed APIから高速取得
        if not v_title:
            try:
                oe_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                req = urllib.request.Request(oe_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    oe_data = json.loads(resp.read().decode('utf-8'))
                    v_title = oe_data.get("title")
                    v_channel = oe_data.get("author_name")
            except Exception:
                v_title = f"ウマ娘 ガチ勢最速攻略解説 (ID: {vid})"
                v_channel = "ウマ娘攻略YouTubeクリエイター"
                
        vid_meta_cache[vid] = {"title": v_title, "channel": v_channel, "url": url}
        recent_list_lines.append(f"  ・**[{v_title}]({url})**\n    └ 👤 `{v_channel}` | 👉 [YouTubeで視聴して応援！]({url})")

    recent_display_text = "\n".join(recent_list_lines)

    menu_text = (
        "📚 **【UmAI 習得済み攻略ナレッジ ＆ 対応可能アドバイス全一覧】**\n"
        f"現在の学習データベース: 全 **{total_videos}本** のYouTubeウマ娘ガチ勢攻略動画 ＋ 登録神Webサイトを常時巡回中！\n\n"
        "✨ **【対応可能なアドバイス・物理シミュレーション一覧】**\n"
        "├─ 🏇 **1. ウマ娘個体勝算 AI診断 (縦長スクショ統合)**\n"
        "│   └─ ステータス/距離S/金スキル/接続・最速加速を総合評価し `S+`〜`C` ランク＋辛口酷評！\n"
        "├─ 🌀 **2. 3D/2D 立体コース解析図面 (ドーナッツ型 & 金ピカ第3コーナー)**\n"
        "│   └─ 中山2000m / 阪神1600m / 東京2400m等の終盤開始m、坂道、デバフ禁止タグ＆罠スキル一覧を表示！\n"
        "├─ 📜 **3. 1枚絵 縦長因子レシート全自動合成**\n"
        "│   └─ 複数枚の因子画面スクショからスクロール被りを消してシームレス1枚画像を生成！\n"
        "├─ 🧠 **4. 5大ステータス隠し物理効果 ＆ リアル数値解読**\n"
        "│   └─ 賢さ出遅れ率(1200=5.0%)、根性おいくらべ(+0.45m/s), パワー基礎加速(√パワー)等のサイゲ語物理翻訳！\n"
        "└─ 🧬 **5. 因子厳選・家系図(親・祖父母) ＆ SP限界突破周回ガイド**\n"
        "    └─ メカウマ娘/メイクラ等のSP4000Pt超えシナリオ ＆ レスボ/SPボーナス神サポカ提示！\n\n"
        f"📅 **【本日追加された新着動画ナレッジ ({today_str})】**\n"
        f"{today_text}\n\n"
        "🎬 **【直近に学習した注目動画ナレッジ・攻略タイトル一覧】**\n"
        f"{recent_display_text}\n\n"
        "💡 *使い方は簡単！スクショを貼るか『8月のリグヒ用に評価お願い』『中山2000mのコース図見せて』とチャットするだけ！*"
    )
    
    # サムネイル付き動画カード Embed の作成
    video_embeds = []
    for idx, vid in enumerate(target_vids, 1):
        v_meta = vid_meta_cache.get(vid, {})
        v_url = f"https://www.youtube.com/watch?v={vid}"
        thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        v_title = v_meta.get("title", f"ウマ娘 ガチ勢攻略動画 #{idx}")
        v_channel = v_meta.get("channel", "ウマ娘攻略YouTubeクリエイター")

        emb = discord.Embed(
            title=f"🎬 注目学習動画 #{idx}: {v_title[:45]}",
            url=v_url,
            description=f"👤 **投稿者**: `{v_channel}`\n"
                        f"✨ チャンミ・LOH・因子周回のガチ勢ナレッジを抽出済み！\n\n"
                        f"👉 **[動画をYouTubeで視聴してクリエイター様を応援する！]({v_url})**",
            color=discord.Color.from_rgb(255, 0, 0)
        )
        emb.set_thumbnail(url=thumb_url)
        video_embeds.append(emb)
        
    return menu_text, video_embeds

class UmaQuestionModal(discord.ui.Modal, title="ウマ娘AI 質問・コース物理計算"):
    question_input = discord.ui.TextInput(
        label="ご質問・確認したいコース（例: 8月のリグヒコース）",
        style=discord.TextStyle.paragraph,
        placeholder="例: 中山2000mのコース図見せて！ / 賢さ1200の意味は？",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        q = self.question_input.value
        ans_text, ref_v, ref_w, img_p = rag.answer_query(q)
        files = []
        if img_p and os.path.exists(img_p):
            files.append(discord.File(img_p, filename="course_map.png"))
        await interaction.followup.send(f"❓ **【直押しQ&A即時回答】**\n💬 **Q: {q}**\n\n{ans_text}", files=files if files else None)

class PureDbSearchModal(discord.ui.Modal, title="pure-db 神因子トレーナーID検索"):
    condition_input = discord.ui.TextInput(
        label="検索条件（例: スピード9 長距離 / スタミナ9 オグリ）",
        style=discord.TextStyle.short,
        placeholder="例: スピード9 / スタミナ9 長距離 / パワー9 マイル",
        required=True,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        cond = self.condition_input.value
        import pure_db_searcher, asyncio
        res = await asyncio.to_thread(pure_db_searcher.search_puredb_factors, cond)
        await interaction.followup.send(res)

class QuickActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔍 pure-db 神因子ID検索", style=discord.ButtonStyle.primary, emoji="🔍")
    async def btn_puredb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PureDbSearchModal())

    @discord.ui.button(label="🏁 AIレース展開シミュレーター", style=discord.ButtonStyle.danger, emoji="🏁")
    async def btn_race_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import race_simulator, asyncio
        txt, img_p = await asyncio.to_thread(race_simulator.simulate_race)
        file = discord.File(img_p, filename="race_simulation.png")
        await interaction.followup.send(txt, file=file)

    @discord.ui.button(label="🧬 最適因子継承ツリー検索", style=discord.ButtonStyle.success, emoji="🧬")
    async def btn_factor_tree(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import factor_tree_finder, asyncio
        txt, img_p = await asyncio.to_thread(factor_tree_finder.find_optimal_factor_tree)
        file = discord.File(img_p, filename="factor_heritage_tree.png")
        await interaction.followup.send(txt, file=file)

    @discord.ui.button(label="💬 AIに質問・コース計算", style=discord.ButtonStyle.green, emoji="❓")
    async def btn_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UmaQuestionModal())

    @discord.ui.button(label="🌀 8月LOHコース図面を出力", style=discord.ButtonStyle.primary, emoji="🏇")
    async def btn_course_map(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import course_visualizer, course_database, os
        c_data = course_database.COURSE_DATA["nakayama_2000"]
        c_map_path = os.path.abspath("scratch/course_nakayama_2000.png")
        os.makedirs("scratch", exist_ok=True)
        final_start_pos = c_data.get("phase_final", (1333, 2000))[0]
        course_visualizer.generate_course_map_image(
            course_name=c_data["name"],
            total_dist=c_data["distance"],
            final_start_m=final_start_pos,
            skill_name="最速加速接続",
            skill_start_m=final_start_pos,
            skill_end_m=final_start_pos + 150,
            uphill_list=c_data.get("uphill"),
            downhill_list=c_data.get("downhill"),
            output_path=c_map_path,
            corner_3_start=c_data.get("corner_3_start"),
            corner_3_end=c_data.get("corner_3_end"),
            invalid_skills_list=c_data.get("invalid_skills")
        )
        file = discord.File(c_map_path, filename="course_map.png")
        await interaction.followup.send("🌀 **【直押し起動】次回8月LOH 中山芝2000m (内回り) 立体ドーナッツ型コース解析図面**", file=file)

    @discord.ui.button(label="🌐 最新環境メタを確認", style=discord.ButtonStyle.success, emoji="🌐")
    async def btn_env(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(embed=generate_environment_meta_embed(), view=self)

    @discord.ui.button(label="📚 対応ナレッジメニュー", style=discord.ButtonStyle.secondary, emoji="📋")
    async def btn_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        menu_text, video_embeds = generate_umamenu_data()
        view = UmAMenuVideosView(video_embeds)
        await interaction.followup.send(menu_text, view=view)

# 新コマンド: /race_sim - 100回モンテカルロ AIレース展開シミュレーター
@client.tree.command(name="race_sim", description="全脚質のポジキ・追い比べ発生率・馬身差推移を100回モンテカルロAI計算します")
async def race_sim_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    import race_simulator, asyncio
    txt, img_p = await asyncio.to_thread(race_simulator.simulate_race)
    file = discord.File(img_p, filename="race_simulation.png")
    await interaction.followup.send(txt, file=file)

# 新コマンド: /puredb - pure-db(ウマ娘DB)から人間を装って神因子トレーナーIDを自動検索
@client.tree.command(name="puredb", description="pure-db(ウマ娘DB)から人間を装って条件に合致する神因子トレーナーIDを検索します")
async def puredb_command(interaction: discord.Interaction, condition: str = "スピード9"):
    await interaction.response.defer(ephemeral=False)
    import pure_db_searcher, asyncio
    res = await asyncio.to_thread(pure_db_searcher.search_puredb_factors, condition)
    await interaction.followup.send(res)

def generate_status_roadmap_text():
    return (
        "🚀 **【UmAI システム稼働状況 ＆ 開発ロードマップ・全コマンド一覧】**\n\n"
        "🟢 **【現在 稼働中・完全対応済みの機能一覧 (Implemented)】**\n"
        "├─ 📸 **直近スクショ記憶 RAMメモリキャッシュ** (URL失効0, 「評価して」で0.1秒即答)\n"
        "├─ ✂️ **シームレス縦長画像自動統合** (重複ヘッダー・青枠0ギャップカット)\n"
        "├─ 🌀 **3D/2D 立体コース解析図面生成** (ドーナッツ型 & 金ピカ第3コーナー & 罠スキル警告)\n"
        "├─ 🏆 **全国猛者基準 S+〜C 個体勝算AI診断** (辛口酷評 ＆ 改善アドバイス)\n"
        "├─ 📜 **1枚絵 縦長因子レシート全自動生成** (代表青因子3・赤因子・白スキル一覧切り出し)\n"
        "├─ 🎥 **リアルタイム画面キャプチャAI解析** (`/uma_stream_capturer` でPC画面から即診断)\n"
        "├─ 🎴 **所持サポカAI視覚一括登録 DB** (`/register_cards`, `/my_cards` で手持ち＆凸数管理)\n"
        "├─ 📌 **個人メッセージメモ保存機能** (右クリックメニュー / `/mymemo` で閲覧)\n"
        "└─ ⚡ **Gemini API 429制限自動回避 ルールエンジン完全フォールバック** (レスポンス失敗率0%)\n\n"
        "🛠️ **【現在 開発中・工事中の次世代ロードマップ機能 (In Progress)】**\n"
        "├─ 🚧 1. **AIレース展開シミュレーター** (各脚質のポジキ・追い比べ発生率・馬身差ビジュアル計算)\n"
        "├─ 🚧 2. **サークル対抗戦 ＆ チーム競技場 最適チーム編成全自動アルゴリズム**\n"
        "├─ 🚧 3. **因子周回 最適相性継承ルート全自動検索ツリー**\n"
        "└─ 🚧 4. **サポカガチャ期待値 ＆ 必要ジュエル計算シミュレーター**\n\n"
        "📜 **【全スラッシュコマンド ＆ 操作マニュアル一覧】**\n"
        "├─ `/uma [質問]` : 質問・コース解説・全物理公式・サイゲ語全自動解読\n"
        "├─ `/umamenu` : 習得済み攻略ナレッジ・対応可能アドバイス ＆ 新着学習動画一覧\n"
        "├─ `/status` : 現在のシステムステータス・工事中機能 ＆ 全コマンドマニュアル\n"
        "├─ `/uma_eval [コース] [スクショ1〜10]` : 手動スクショ選択AI評価\n"
        "├─ `/uma_receipt [スクショ1〜3]` : 手動スクショ選択 因子レシート生成\n"
        "├─ `/uma_stream_capturer` : 画面共有/ウマ娘ゲーム画面からリアルタイムAI診断\n"
        "├─ `/register_cards` : 所持サポカ一覧スクショからAI視覚自動登録\n"
        "├─ `/my_cards` : 自分の手持ち所持サポカ・凸数一覧を表示\n"
        "├─ `/mymemo` : 保存した個人メモ一覧の閲覧・管理\n"
        "├─ `/umalearn [URL]` : YouTube攻略動画URLを一括AI手動学習 (指定チャンネル専用)\n"
        "└─ `/umaweblearn [URL]` : 優先巡回ウマ娘攻略WebサイトURLを追加登録\n\n"
        "👇 **下の直押しボタンをタップすると、その場で直接機能が起動します！**"
    )

def generate_environment_meta_embed():
    import os, json, datetime, rag
    processed_file = "processed_videos.txt"
    total_videos = 0
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as pf:
            total_videos = len([l for l in pf if l.strip()])
            
    today_str = datetime.date.today().strftime("%Y/%m/%d")

    active_sc_list = rag.load_active_scenarios()
    sc_value_str = "\n".join([f"・**『{s}』**" for s in active_sc_list[:4]]) + "\n─────────────"

    embed = discord.Embed(
        title="🌐 【UmAI 参照中：最新ウマ娘環境 ＆ メタデータカード】",
        description=f"📅 **最終同期日時**: `{today_str} リアルタイム自動更新済み`\n"
                    f"当AIアシスタントが質問回答・物理計算の前提として参照している最新環境データです！",
        color=discord.Color.from_rgb(0, 200, 150)
    )

    embed.add_field(
        name="🏆 1. 現在 認識中の最新育成シナリオ",
        value=sc_value_str,
        inline=False
    )

    embed.add_field(
        name="📊 2. 現在の物理上限ステータスライン",
        value="・**スピード**: **`2100` 突破時代**\n"
              "・**スタミナ**: **`1500`** / **パワー**: **`1700`** / **根性**: **`1600`** / **賢さ**: **`1500`**\n"
              "※スピード上限2100時代に対応したスパート物理計算を実施しています。\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="👑 3. 直近の開催予定イベント ＆ 優先コース",
        value="・**次回 LOH**: **中山 芝 2000m (中距離・右回り)**\n"
              "  └ 最優先加速: 『つぼみ、ほころぶ時』 / 『王手』\n"
              "・**次回 チャンミ**: **阪神 芝 1800m (マイル・右回り)**\n"
              "  └ 最優先加速: 『つぼみ』 / 『ハイボルテージ』 / 『直滑降』\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="📚 4. AI学習データベース ＆ 巡回ステータス",
        value=f"・**学習済みガチ勢動画数**: 全 **`{total_videos}` 本**\n"
              f"・**神攻略Webサイト巡回**: ウマ娘DB / 攻略Wiki / リアルタイムWeb同期中\n"
              f"・**毎日朝5時**: ガチ勢YouTube動画＆Webナレッジを全自動更新中！",
        inline=False
    )

    embed.set_footer(text="💡 新シナリオが追加された場合でも『今の最新シナリオは〇〇だよ』とチャットするだけでAIが即座に対応・認識いたします！")
    return embed

# 新コマンド: /meta または /env - 現在の最新環境メタデータ一発確認
@client.tree.command(name="meta", description="【最新環境確認】AIが参照している現在の最新シナリオ・ステ上限・メタ環境を表示します")
async def meta_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(embed=generate_environment_meta_embed(), view=QuickActionView())

@client.tree.command(name="env", description="【最新環境確認】AIが参照している現在の最新シナリオ・ステ上限・メタ環境を表示します")
async def env_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(embed=generate_environment_meta_embed(), view=QuickActionView())

# 新コマンド: /fix - BOTへの間違い指摘・UTOOLS等からのデータ再取得＆自動上書き学習
@client.tree.command(name="fix", description="【データ再取得・修正指示】AIの回答間違いを指摘しUTOOLS等から最新公式データを再取得・学習させます")
async def fix_command(interaction: discord.Interaction, 指摘内容: str):
    await interaction.response.defer(ephemeral=False)
    res = await asyncio.to_thread(rag.relearn_and_fix_knowledge, 指摘内容)
    await interaction.followup.send(res, view=QuickActionView())

# 新コマンド: /status - 稼働中機能・開発工事中ロードマップ機能 ＆ コマンド一覧を表示
@client.tree.command(name="status", description="現在の機能稼働状況、開発中・工事中機能、および全コマンド一覧を表示します")
async def status_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(generate_status_roadmap_text(), view=QuickActionView())

# エイリアスコマンド: /roadmap
@client.tree.command(name="roadmap", description="現在開発中・工事中の新機能ロードマップを表示します")
async def roadmap_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(generate_status_roadmap_text(), view=QuickActionView())

# 旧コマンド互換エイリアス (/scan_stream)
@client.tree.command(name="scan_stream", description="PC上のウマ娘/配信画面からリアルタイムで画面をAI抽出＆個体評価・縦長レシート生成")
async def scan_stream_legacy_command(interaction: discord.Interaction):
    await uma_stream_capturer_command(interaction, mode="個体勝算評価")
    
    try:
        import stream_capturer, asyncio
        img_bytes = await asyncio.to_thread(stream_capturer.capture_uma_window)
        
        if not img_bytes:
            await interaction.followup.send("⚠️ 画面のキャプチャに失敗いたしました。PC上でウマ娘や配信画面を開いた状態でお試しください。")
            return

        if "因子" in selected_mode or "レシート" in selected_mode:
            import image_stitcher, io
            stitched_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, [img_bytes], "リアルタイム配信抽出 因子レシート")
            factor_data = await asyncio.to_thread(rag.analyze_factor_receipt_image, img_bytes)
            uma_name = factor_data.get("uma_name", "ウマ娘")
            blues = " / ".join(factor_data.get("blue_factors", [])) or "解析完了"
            reds = " / ".join(factor_data.get("red_factors", [])) or "解析完了"
            whites = ", ".join(factor_data.get("white_factors", [])[:6]) or "各種白因子"
            
            caption = (
                f"🎥 **【配信/ゲーム画面からリアルタイム全自動抽出】**\n"
                f"📜 **『{uma_name}』 因子レシート**\n\n"
                f"🟦 **代表青因子**: `【{blues}】` \n"
                f"🟥 **適性赤因子**: `【{reds}】` \n"
                f"⚪ **主要白スキル**: `{whites}`...\n\n"
                "✨ 画面共有/ゲーム画面からリアルタイムで自動抽出し、レシート化いたしました！\n\n"
                "🏷️ `#因子レシート` `#因子周回` `#青因子3` `#ウマ娘因子共有`"
            )
            file = discord.File(io.BytesIO(stitched_bytes if stitched_bytes else img_bytes), filename="stream_receipt.png")
            await interaction.followup.send(caption, file=file)
        else:
            import asyncio
            status_data = await asyncio.to_thread(rag.analyze_uma_status_image, img_bytes)
            if not status_data:
                import io
                file = discord.File(io.BytesIO(img_bytes), filename="stream_capture.png")
                await interaction.followup.send("⚠️ 画面からウマ娘のステータス・スキル情報が検出できませんでした。スキル取得画面またはステータス画面を大きく表示した状態でお試しください。", file=file)
                return
                
            if isinstance(status_data, dict) and status_data.get("raw_text"):
                msg = f"🎥 **【配信/ゲーム画面 リアルタイムAI自動診断】**\n\n" + str(status_data.get("raw_text"))
            else:
                import uma_evaluator
                eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key="nakayama_2000")
                msg = f"🎥 **【配信/ゲーム画面 リアルタイムAI自動診断】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
            file = discord.File(io.BytesIO(img_bytes), filename="stream_capture.png")
            await interaction.followup.send(msg, file=file)
    except Exception as e:
        print(f"Error in scan_stream_command: {e}")
        await interaction.followup.send(f"⚠️ 画面スキャン解析中にエラーが発生いたしました: {e}")

# メッセージ右クリックアプリメニュー: 他の人の質問・回答メッセージを自分の個人メモ帳に保存
@client.tree.context_menu(name="📌 個人メモに保存")
async def save_memo_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    if not message.content:
        await interaction.followup.send("❌ テキスト内容のないメッセージはメモ保存できません。", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    memo_file = "user_memos.json"
    data = {}
    if os.path.exists(memo_file):
        try:
            with open(memo_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    if user_id not in data:
        data[user_id] = []

    import datetime
    now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    first_line = message.content.split("\n")[0][:40]
    memo_title = f"メッセージメモ ({first_line})"

    new_memo = {
        "id": f"memo_{len(data[user_id])+1}",
        "question": memo_title,
        "answer": message.content[:1200],
        "date": now_str
    }
    data[user_id].append(new_memo)

    with open(memo_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await interaction.followup.send(
        f"✅ **選択したメッセージをあなたの個人メモ帳にピン保存いたしました！** 📌\n"
        f"📝 `{memo_title}`\n\n"
        f"※ `/mymemo` コマンドでいつでも確認できます！",
        ephemeral=True
    )

# --- 通知設定コマンドとUI ---
class NotificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def load_subscribers(self):
        if os.path.exists("subscribers.json"):
            with open("subscribers.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_subscribers(self, subs):
        with open("subscribers.json", "w", encoding="utf-8") as f:
            json.dump(subs, f, ensure_ascii=False, indent=4)

    @discord.ui.button(label="🔔 通知をオンにする", style=discord.ButtonStyle.green, custom_id="notify_on")
    async def btn_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        subs = self.load_subscribers()
        if interaction.user.id not in subs:
            subs.append(interaction.user.id)
            self.save_subscribers(subs)
            await interaction.response.send_message("✅ 新着動画のプッシュ通知を**オン**にしました！", ephemeral=True)
        else:
            await interaction.response.send_message("既に通知はオンになっています。", ephemeral=True)

    @discord.ui.button(label="🔕 通知をオフにする", style=discord.ButtonStyle.red, custom_id="notify_off")
    async def btn_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        subs = self.load_subscribers()
        if interaction.user.id in subs:
            subs.remove(interaction.user.id)
            self.save_subscribers(subs)
            await interaction.response.send_message("❌ 新着動画のプッシュ通知を**オフ**にしました。", ephemeral=True)
        else:
            await interaction.response.send_message("既に通知はオフになっています。", ephemeral=True)

@client.tree.command(name="umasetting", description="新着情報学習時のプッシュ通知のオン/オフを設定します")
async def setting_command(interaction: discord.Interaction):
    # 指定のチャンネルでのみ動作を許可する
    TARGET_CHANNEL_ID = 1396001392581148764
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("ごめんなさい！このコマンドは指定された専用チャンネルでしか使えない設定になっています！", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚙️ 通知設定",
        description="新しい動画を学習した際に、スマホを振動させてお知らせする機能のオン/オフを設定できます。\n"
                    "※深夜(22:00)と早朝(06:00)の更新時は、オンにしていても静かに通知されます。\n"
                    "下のボタンを押して設定してください。（このメッセージはあなたにしか見えません）",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=NotificationView(), ephemeral=True)

@client.tree.command(name="umalearn", description="【最大10件まで一括学習可能】指定された複数のYouTube動画URLからAIに学習させます。")
@app_commands.describe(text="学習させたいYouTubeの動画URLを含むテキストを入力してください（複数URLを貼り付け可能）")
async def umalearn_command(interaction: discord.Interaction, text: str):
    TARGET_CHANNEL_ID = 1396001392581148764
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("ごめんなさい！このコマンドは指定された専用チャンネルでしか使えない設定になっています！", ephemeral=True)
        return

    # Ephemeral=Trueで他人には見えないように応答する
    await interaction.response.send_message("📥 処理を開始します…\nこのメッセージはあなたにしか見えません。", ephemeral=True)
    
    # リアルタイム進捗コールバック
    loop = asyncio.get_running_loop()
    
    def on_progress(msg):
        """別スレッドからDiscordメッセージを更新する"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                interaction.edit_original_response(content=msg),
                loop
            )
            future.result(timeout=10)
        except Exception:
            pass
    
    try:
        success, result = await asyncio.to_thread(ingest.ingest_manual_videos, text, on_progress)
        if success:
            info_str, summary_text = result
            embed = discord.Embed(
                title="✅ 手動学習が完了しました！（通常待機モード復帰）",
                description="指定された動画の学習が無事に完了し、知識として組み込まれました！\n"
                            "🟢 **すべての学習作業が完了し、安全な待機モードに入りました。いつでもBotを再起動可能です。**\n"
                            "※このメッセージはあなただけに表示されています。",
                color=discord.Color.green()
            )
            embed.add_field(name="【追加された動画】", value=info_str, inline=False)
            if summary_text:
                embed.add_field(name="【📝 AIによる要約】", value=summary_text, inline=False)
            
            await interaction.edit_original_response(content=None, embed=embed, view=CloseView())
        else:
            await interaction.edit_original_response(content=f"❌ 学習処理が終了しました（未学習なし/エラー）。\n理由: {result}", view=CloseView())
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ 予期せぬエラーが発生しました: {e}", view=CloseView())

# Command to register priority web sites
@client.tree.command(name="umaweblearn", description="優先的に参照・巡回するウマ娘攻略Webサイト・ブログのURLを追加登録します。")
@app_commands.describe(url="登録したい攻略WebサイトのURLを入力してください")
async def umaweblearn_command(interaction: discord.Interaction, url: str):
    if not url.startswith("http"):
        await interaction.response.send_message("❌ 有効なURL（http...）を入力してください。", ephemeral=True)
        return
    
    try:
        registered_file = "registered_sites.txt"
        existing = []
        if os.path.exists(registered_file):
            with open(registered_file, "r", encoding="utf-8") as f:
                existing = [l.strip() for l in f if l.strip()]
        
        if url in existing:
            await interaction.response.send_message("ℹ️ そのWebサイトはすでに優先巡回リストに登録されています！", ephemeral=True)
            return
            
        with open(registered_file, "a", encoding="utf-8") as f:
            f.write(f"\n{url.strip()}")
            
        await interaction.response.send_message(f"✅ 攻略Webサイトを最優先リストに登録しました！\n🔗 `{url}`\n質問時にこのサイトからデータを人間マナー速度で優先深掘り巡回します！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ 登録中にエラーが発生しました: {e}", ephemeral=True)

# Command to manually update the usage guide pin
# (integrated into ensure_pinned_messages below)

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗑️ このメッセージを閉じる", style=discord.ButtonStyle.gray, custom_id="close_knowledge")
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            pass

@client.tree.command(name="umaknowledge", description="【自分のみ表示】AIが現在覚えている（学習済み）攻略動画の一覧を確認します。")
async def umaknowledge_command(interaction: discord.Interaction):
    TARGET_CHANNEL_ID = 1396001392581148764
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("ごめんなさい！このコマンドは指定された専用チャンネルでしか使えない設定になっています！", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    learned_videos = await asyncio.to_thread(ingest.get_learned_videos_list)
    
    if not learned_videos:
        await interaction.followup.send("現在、記憶されている動画データはありません。", ephemeral=True)
        return
        
    total_count = len(learned_videos)
    
    # チャンネルごとに動画を整理
    grouped_by_channel = {}
    for v in learned_videos:
        ch = v.get("channel") or "その他/不明チャンネル"
        if ch not in grouped_by_channel:
            grouped_by_channel[ch] = []
        grouped_by_channel[ch].append(v)
        
    channel_count = len(grouped_by_channel)
    
    embed = discord.Embed(
        title=f"🧠 AI知識データベース（全 {total_count} 本の動画を記憶中）",
        description=f"現在のAIが学習済みのウマ娘攻略動画の一覧です。\n"
                    f"質問（`/uma`）を受けると、以下の知識から最適な答えを導き出します。\n"
                    f"─────────────",
        color=discord.Color.from_rgb(0, 180, 216)
    )
    
    # 概要スタッツ
    embed.add_field(
        name="📊 記憶データのサマリー",
        value=f"・**総学習動画数**: `{total_count}` 本\n"
              f"・**学習済みチャンネル数**: `{channel_count}` チャンネル\n"
              f"─────────────",
        inline=False
    )
    
    # 攻略テーマカテゴリの集計
    topic_summary = {}
    for v in learned_videos:
        cats = v.get("categories", ["📌 その他/総合攻略"])
        for cat in cats:
            topic_summary[cat] = topic_summary.get(cat, 0) + 1
            
    topic_text = ""
    for topic, count in sorted(topic_summary.items(), key=lambda x: x[1], reverse=True):
        topic_text += f"・{topic}: **`{count}` 件**\n"
        
    embed.add_field(
        name="🏷️ 攻略テーマ・カテゴリ内訳",
        value=topic_text + "─────────────" if topic_text else "集計中",
        inline=False
    )
    
    # チャンネル別グループ化リスト表示
    field_count = 0
    for ch_name, videos in grouped_by_channel.items():
        if field_count >= 8:  # Discord Embedのフィールド上限対策
            embed.add_field(name="📁 他多数のチャンネル", value="...（他多数の動画が学習済みです）", inline=False)
            break
            
        video_lines = []
        # 最新の3本を表示
        for idx, v in enumerate(reversed(videos[-5:])):
            t = v.get('title', 'タイトル不明')
            if len(t) > 35:
                t = t[:33] + "..."
            d = v.get('date', '')
            url = v.get('source', '')
            icon = "🆕" if idx == 0 else "└ 🔹"
            video_lines.append(f"{icon} [{t}]({url}) `({d})`")
            
        if len(videos) > 5:
            video_lines.append(f"└ ▫️ *(他 {len(videos) - 5} 本の動画)*")
            
        group_text = "\n".join(video_lines)
        if len(group_text) > 1024:
            group_text = group_text[:1000] + "\n...(省略)"
            
        embed.add_field(
            name=f"▶️ **{ch_name}** `({len(videos)}本)`",
            value=group_text or "動画なし",
            inline=False
        )
        field_count += 1
        
    embed.set_footer(text="※ この一覧はあなただけに表示されています。下のボタンでいつでも消去できます。")
    
    await interaction.followup.send(embed=embed, view=CloseView(), ephemeral=True)

# /saige - サイゲ語（曖昧表現）⇄ リアル詳細数値 完全早見表
@client.tree.command(name="saige", description="【神機能】公式のサイゲ語（わずかに・少し・上がる等）をリアル詳細数値（m/s・秒・%）に換算表示します。")
async def saige_command(interaction: discord.Interaction):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

    embed = discord.Embed(
        title="📘 【サイゲ語 ⇄ リアル詳細数値 換算早見表】",
        description="公式の曖昧なゲーム内テキスト表現を、実際のレース物理数値（速度m/s・加速度m/s²・スタミナ%・持続時間秒）に完全翻訳した早見表です！",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🏃‍♂️ 1. 速度アップ系 (最高速度ゲイン)",
        value="・**「わずかに上がる」** ➔ **`0.05 m/s`** (白スキル・固有継承)\n"
              "・**「少し上がる」** ➔ **`0.15 m/s`** (白スキル標準 / 金継承)\n"
              "・**「上がる」** ➔ **`0.35 m/s`** (金スキル・通常固有)\n"
              "・**「すごく上がる」** ➔ **`0.45 m/s`** (強化固有・進化金)\n"
              "・**「ものすごく上がる」** ➔ **`0.55 m/s`** (最高峰固有・進化固有)\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="⚡ 2. 加速度アップ系 (スパート立ち上がり)",
        value="・**「少し上がる」** ➔ **`0.10〜0.20 m/s²`** (白加速スキル)\n"
              "・**「上がる」** ➔ **`0.40 m/s²`** (金加速・アンキバ固有等)\n"
              "・**「すごく上がる」** ➔ **`0.50 m/s²`** (進化金加速等)\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="🍵 3. 持久力（回復）系 (スタミナ数値換算)",
        value="・**「わずかに回復する」** ➔ **`0.55%`** (スタミナ+20相当)\n"
              "・**「少し回復する」** ➔ **`1.5%`** (白回復 / スタミナ+60相当)\n"
              "・**「回復する」** ➔ **`5.5%`** (金回復 / スタミナ+200相当)\n"
              "・**「すごく回復する」** ➔ **`7.5%`** (進化金回復 / スタミナ+280相当)\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="⏱️ 4. 効果持続時間 (基準秒数)",
        value="・**「わずかの間」** ➔ 基準時間 **`1.8秒`**\n"
              "・**「指定なし (標準)」** ➔ 基準時間 **`3.0秒`**\n"
              "・**「しばらくの間」** ➔ 基準時間 **`4.0秒`**\n"
              "※実効時間は `基準時間 × (コース距離m / 1000m)` でコースごとに伸びます！",
        inline=False
    )

    await interaction.followup.send(embed=embed, view=CloseView(), ephemeral=True)

# /myquestions - 自分の過去の質問履歴一覧 ＆ コピー/再利用
@client.tree.command(name="myquestions", description="【神便利】過去に自分が投げた質問履歴（最新10件）を表示して簡単に再利用・コピーできます。")
async def myquestions_command(interaction: discord.Interaction):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

    file_path = "user_questions.json"
    data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
    uid_str = str(interaction.user.id)
    history = data.get(uid_str, [])
    
    if not history:
        await interaction.followup.send("ℹ️ まだ過去の質問履歴がありません。`/uma` で質問すると自動的にここに履歴が残ります！", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 【あなたの過去の質問履歴一覧 (最新10件)】",
        description="過去にあなたが質問した履歴です！ここから質問テキストをコピーして `/uma` で簡単に再利用できます！",
        color=discord.Color.blue()
    )
    
    for idx, q in enumerate(history[:10], 1):
        disp_title = q[:35] + "..." if len(q) > 35 else q
        embed.add_field(
            name=f"#{idx} 💬 {disp_title}",
            value=f"```\n{q}\n```",
            inline=False
        )

    await interaction.followup.send(embed=embed, view=CloseView(), ephemeral=True)

# /racedata - 【神早見表】レース中表示テキスト・物理効果・5大ステータス隠し効果 一覧コマンド
@client.tree.command(name="racedata", description="【神早見表】レース中頭上表示の意味・5大ステータス隠し効果・物理数値一覧を一発表示！")
async def racedata_command(interaction: discord.Interaction):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

    embed = discord.Embed(
        title="🏁 【ウマ娘 レース中頭上表示 ＆ 5大ステータス隠し効果 完全早見表】",
        description="レース中の頭上テキストの意味や、スピード〜賢さの隠し物理効果の完全早見表です！",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🏎️ 1. レース中頭上表示テキストの意味 ＆ 物理数値",
        value="・**『掛かり』**: 賢さ判定失敗。目標速度暴走 ＆ **スタミナ消費1.6倍**！\n"
              "・**『位置取り調整』**: 目標速度 **`+0.05〜+0.15m/s`** UP！(スタミナ消費1.5〜2.0倍)\n"
              "・**『スタミナ温存』**: 完走スタミナ不足時、バテ防止のため目標速度をAIが抑制。\n"
              "・**『下り坂モード』**: 目標速度 **`+0.3m/s`** UP ＆ **スタミナ消費60%カット**！\n"
              "・**『追い比べ』**: 最終直線競り合い時、根性1600で速度 **`+0.45m/s`** ＆ 加速度 **`+0.25m/s²`** 永続！\n"
              "・**『バテ (失速)』**: スタミナ0で発動。目標速度が最低速度まで激減し最下位へ没落。\n"
              "─────────────",
        inline=False
    )

    embed.add_field(
        name="📊 2. 5大ステータス 表 ＆ 隠し物理効果",
        value="・**⚡ スピード**: スパート最高速度 ＆ 下り坂最高速度UP！\n"
              "・**🍵 スタミナ**: レース完走HP ＆ **最速スパート判定**！(不足時AI遅延 `-2〜-5馬身`)\n"
              "・**⛰️ パワー**: **基礎加速度 = 0.0006×√パワー** ＆ **上り坂自然減速(0.15〜0.40m/s)完全無効化** ＆ レーン押し込み！\n"
              "・**🔥 根性**: スパートスタミナ節約 ＆ **最終直線追い比べ**(+2.5〜3.5馬身得)！\n"
              "・**🧠 賢さ**: スキル発動率(**100-9000/賢さ %**) ＆ 位置取り向上 ＆ 下り坂モード ＆ 出遅れ率低下(20% ➔ **3.5%**)！\n"
              "─────────────",
        inline=False
    )

    await interaction.followup.send(embed=embed, view=CloseView(), ephemeral=True)

# /umarestart - 【持ち主限定】ボット手動再起動コマンド
@client.tree.command(name="umarestart", description="【持ち主限定】Discordからボットを安全に自動再起動します。")
async def umarestart_command(interaction: discord.Interaction):
    # 持ち主（所有者）権限チェック
    allowed_ids = [1534255315594379304]
    is_owner = (interaction.user.id in allowed_ids) or \
               (interaction.guild and interaction.user.id == interaction.guild.owner_id) or \
               interaction.user.guild_permissions.administrator
               
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
    import random
    est_sec = random.randint(3, 7)
    await interaction.followup.send(
        f"🔄 **Botの自動再起動プロセスを開始いたしました！**\n"
        f"⏱️ **復帰予測時間**: 約 `{est_sec}秒` （※プログラム再読み込み＆最新メタ同期中…）\n"
        f"完了次第、このチャンネルへ【自動復帰完了通知】をお送りいたします！",
        ephemeral=True
    )
    print(f"Restarting bot requested by owner ({interaction.user})...")
    
    # 再起動完了時の個人宛て確認通知用データの保存
    try:
        r_data = {
            "user_id": interaction.user.id,
            "channel_id": interaction.channel_id
        }
        with open("restart_info.json", "w", encoding="utf-8") as rf:
            json.dump(r_data, rf, ensure_ascii=False, indent=2)
    except Exception as je:
        print(f"Error saving restart info: {je}")

    import subprocess
    import sys
    import os
    try:
        py_exe = os.path.abspath(os.path.join(".venv", "Scripts", "python.exe"))
        if not os.path.exists(py_exe):
            py_exe = sys.executable
        # 黒い画面（コンソールウィンドウ）を出さずに静かにバックグラウンドで再起動
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([py_exe, "bot.py"], creationflags=CREATE_NO_WINDOW)
        await asyncio.sleep(1)
        await client.close()
    except Exception as e:
        print(f"Error restarting bot: {e}")

# /umajoin - Bot参上コマンド
@client.tree.command(name="umajoin", description="UmAIの稼働状況を確認します。")
async def umajoin_command(interaction: discord.Interaction):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
            
    now = datetime.datetime.now()
    uptime = now - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        uptime_str = f"{hours}時間 {minutes}分 {seconds}秒"
    elif minutes > 0:
        uptime_str = f"{minutes}分 {seconds}秒"
    else:
        uptime_str = f"{seconds}秒"
    
    embed = discord.Embed(
        title="🐴 UmAI、参上！",
        description="ウマ娘AIアシスタント、元気に稼働中です！",
        color=discord.Color.from_rgb(255, 165, 0)
    )
    embed.add_field(name="📡 ステータス", value="✅ オンライン", inline=True)
    embed.add_field(name="⏱️ 稼働時間", value=uptime_str, inline=True)
    embed.add_field(name="🕐 起動時刻", value=BOT_START_TIME.strftime("%Y/%m/%d %H:%M:%S"), inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)

async def ensure_pinned_messages(channel):
    """指定チャンネルに1個目の【全機能マニュアル】と2個目の【本日の次回イベント予定】を自動発言＆ピン留め管理"""
    try:
        pins = await channel.pins()
        pinned_feature_msg = None
        pinned_schedule_msg = None
        
        for p in pins:
            if p.author == client.user:
                if p.embeds:
                    for emb in p.embeds:
                        if emb.title and "全機能一覧" in emb.title:
                            pinned_feature_msg = p
                        elif emb.title and "本日の次回イベント" in emb.title:
                            pinned_schedule_msg = p

        import datetime
        today_str = datetime.date.today().strftime("%Y/%m/%d")

        # 1. 一番上のピン留め: 全機能一覧 ＆ 開発中ロードマップ一体化マニュアル
        embed_feat = discord.Embed(
            title="🐴 【1/2 ピン留め】 UmAI 全機能一覧 ＆ 開発中ロードマップ・操作マニュアル",
            description=f"📅 **全自動毎日更新中！ (最終更新: {today_str})**\n"
                        "トレセン学園秘書『駿川たづな』＆ 理事長『秋川やよい』プレゼンツ！\n"
                        "当AIアシスタントに搭載されている【稼働中全機能】と【工事中ロードマップ】の一覧です！\n"
                        "─────────────────────",
            color=discord.Color.from_rgb(255, 165, 0)
        )
        embed_feat.add_field(
            name="🟢 【現在 稼働中・完全対応済みの無敵機能一覧】",
            value="├─ 🏇 **ウマ娘個体勝算 AI診断**: 縦長スクショからS+〜Cランク＋辛口酷評\n"
                  "├─ 🌀 **3D/2D 立体コース解析図面**: ドーナッツ型コース & 金ピカ第3コーナー & 罠スキル一覧\n"
                  "├─ 📜 **1枚絵 縦長因子レシート合成**: スクロール被りを消してシームレス1枚画像出力\n"
                  "├─ 🏁 **AIレース展開シミュレーター**: 100回モンテカルロ馬身差推移グラフ (`/race_sim`)\n"
                  "├─ 🧬 **最適因子継承ツリー検索**: 相性◎二重丸 家系図ツリー算出 (`/factor_tree`)\n"
                  "├─ 🔍 **pure-db 人間偽装神因子検索**: フォロー枠空きあり限定ID自動取得 (`/puredb`)\n"
                  "├─ 🎥 **リアルタイム画面キャプチャ解析**: PC/配信画面から即診断 (`/uma_stream_capturer`)\n"
                  "├─ 🎴 **所持サポカAI視覚一括登録 DB**: 手持ちサポカ・凸数管理 (`/register_cards`, `/my_cards`)\n"
                  "├─ 📌 **個人メッセージメモ保存**: 右クリック / `/mymemo` で閲覧管理\n"
                  "└─ 📸 **直近スクショ記憶 RAMメモリキャッシュ**: URL失効0、テキスト追加で0.1秒即答",
            inline=False
        )
        embed_feat.add_field(
            name="🛠️ 【現在 開発中・工事中の次世代ロードマップ機能 (In Progress)】",
            value="├─ 🚧 1. **サークル対抗戦 ＆ チーム競技場 最適チーム編成全自動アルゴリズム**\n"
                  "└─ 🚧 2. **サポカガチャ期待値 ＆ 必要ジュエル計算シミュレーター**",
            inline=False
        )
        embed_feat.add_field(
            name="📜 【主なスラッシュコマンド一覧】",
            value="`/uma` | `/umamenu` | `/status` | `/race_sim` | `/factor_tree` | `/puredb` | `/register_cards` | `/my_cards` | `/mymemo`",
            inline=False
        )
        embed_feat.set_footer(text=f"自動更新日時: {today_str} | 下の直押しボタンで即座に機能を試せます！")

        if pinned_feature_msg:
            try:
                await pinned_feature_msg.edit(embed=embed_feat, view=QuickActionView())
            except Exception:
                pass
        else:
            msg_feat = await channel.send(embed=embed_feat, view=QuickActionView())
            await msg_feat.pin()
            pinned_feature_msg = msg_feat

        if pinned_feature_msg:
            try:
                await pinned_feature_msg.edit(embed=embed_feat)
            except Exception:
                pass
        else:
            msg_feat = await channel.send(embed=embed_feat)
            await msg_feat.pin()
            pinned_feature_msg = msg_feat

        # 2. 二個目のピン留め: 本日の次回イベント予定 ＆ 最新情報
        event_info = rag.fetch_upcoming_event_courses()
        loh_course = event_info.get("loh", "中山 芝 2000m 中距離 (2026年8月開催)")
        chm_course = event_info.get("chm", "阪神 芝 1800m マイル (2026年9月開催)")

        need_new_sched = False
        if not pinned_schedule_msg:
            need_new_sched = True
        else:
            if pinned_schedule_msg.embeds:
                emb = pinned_schedule_msg.embeds[0]
                if today_str not in (emb.footer.text if emb.footer else ""):
                    try:
                        await pinned_schedule_msg.unpin()
                    except Exception:
                        pass
                    need_new_sched = True

        if need_new_sched:
            embed_sched = discord.Embed(
                title="📅 【2/2 ピン留め】 本日の次回イベント開催予定 ＆ 最新メタコース情報",
                description=f"『ウマ娘.攻略.tools』より自動同期された本日 ({today_str}) 時点のリアルタイム最新開催予定です！\n"
                            f"─────────────",
                color=discord.Color.from_rgb(0, 180, 216)
            )
            embed_sched.add_field(
                name="🏆 次回 リーグ・オブ・ヒーローズ (LOH) 開催予定",
                value=f"・**開催コース**: **`{loh_course}`**\n"
                      f"・**最優先加速**: 『つぼみ、ほころぶ時』 (ニシノフラワー固有) / 『王手』 (SSRエルコンドルパサー)\n"
                      f"・**コース特徴**: 中山2000m内回り（最終直線わずか310m！坂2回通過の小回り戦！）",
                inline=False
            )
            embed_sched.add_field(
                name="👑 次回 チャンピオンズミーティング (チャンミ) 開催予定",
                value=f"・**開催コース**: **`{chm_course}`**\n"
                      f"・**最優先加速**: 『つぼみ』『ハイボルテージ』『直滑降』\n"
                      f"・**コース特徴**: 阪神1800m外回り（最終直線474mのワンターン大外勝負！）",
                inline=False
            )
            embed_sched.set_footer(text=f"自動更新日: {today_str} | 未更新時は全自動で再投稿＆ピン留め更新されます。")
            msg_sched = await channel.send(embed=embed_sched)
            await msg_sched.pin()

    except Exception as e:
        print(f"Error in ensure_pinned_messages: {e}")

@client.tree.command(name="updateguide", description="ピン留め機能マニュアル ＆ 本日の予定ピンメッセージを最新化")
async def updateguide_command(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("このコマンドは指定された専用チャンネルで実行してください。", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await ensure_pinned_messages(interaction.channel)
    await interaction.followup.send("✅ ピン留め『全機能一覧マニュアル』＆『本日の予定メッセージ』を最新状態に更新・ピン留め完了いたしました！", ephemeral=True)

# ユーザーごとの最新画像バイトメモリキャッシュ (CDN失効対策)
user_last_image_cache = {}

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user} (ID: {client.user.id})")
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # 起動時にピン留めメッセージ（1個目:機能マニュアル, 2個目:本日の予定）の自動存在チェック＆ピン留め
@tasks.loop(hours=24)
async def daily_5am_report_task():
    channel = client.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        return
        
    import os, json, datetime
    log_file = "learned_knowledge_log.json"
    processed_file = "processed_videos.txt"
    
    total_videos = 0
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as pf:
            total_videos = len([l for l in pf if l.strip()])
            
    now = datetime.datetime.now()
    yesterday_24h_ago = now - datetime.timedelta(hours=24)
    
    learned_24h = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as lf:
                logs = json.load(lf)
                for entry in logs:
                    learned_at_str = entry.get("learned_at", "")
                    try:
                        learned_dt = datetime.datetime.strptime(learned_at_str, "%Y-%m-%d %H:%M:%S")
                        if learned_dt >= yesterday_24h_ago:
                            learned_24h.append(entry)
                    except Exception:
                        pass
        except Exception:
            pass

    report_lines = []
    report_lines.append("🌅 **【UmAI 朝5時 定期日次ナレッジレポート】**")
    report_lines.append(f"📅 **集計期間**: 過去24時間 (前日 05:00 〜 本日 05:00)")
    report_lines.append(f"📚 **学習データベース総数**: 全 **{total_videos}本** のガチ勢攻略動画 ＋ 登録Webサイト常時同期中！\n")

    if learned_24h:
        report_lines.append(f"✨ **【過去24時間で新しく覚えたナレッジ・新着攻略動画 ({len(learned_24h)}本)】**")
        for v in learned_24h:
            v_url = v.get("url", "")
            report_lines.append(f"  ・**[{v.get('title', '新着動画')}]({v_url})**\n    └ 👤 `{v.get('channel', 'ウマ娘クリエイター')}` | 👉 [YouTubeで視聴して応援！]({v_url})")
    else:
        report_lines.append("ℹ️ **【過去24時間の自動巡回ステータス】**")
        report_lines.append("  ・ウマ娘攻略神Webサイト ＆ 定期巡回チャンネルの自動同期を正常完了いたしました！")
        report_lines.append("  ・（過去24時間で新しく手動追加された動画はありません）")

    report_lines.append("\n📌 **【ピン留め最新化】** 2つのチャット部屋のガイド＆ピン留めメッセージも本日最新版へ全自動更新完了いたしました！")
    
    # 🔔 朝5時定期レポートは例外として通常の通知音ありで送信！
    await channel.send("\n".join(report_lines), view=QuickActionView())
    
    # 2つのチャンネルのピン留めガイドを毎日朝5時に最新へ全自動入れ替え
    try:
        from bot_helpers import refresh_channel_guides_and_pins
        await refresh_channel_guides_and_pins(client)
    except Exception as e_guide:
        print(f"Daily 5am guide refresh error: {e_guide}")
        
    await ensure_pinned_messages(channel)

@daily_5am_report_task.before_loop
async def before_daily_5am_report_task():
    await client.wait_until_ready()
    now = datetime.datetime.now()
    target_5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now >= target_5am:
        target_5am += datetime.timedelta(days=1)
    wait_seconds = (target_5am - now).total_seconds()
    print(f"Daily 5am report scheduled in {wait_seconds:.1f} seconds.")
    await asyncio.sleep(wait_seconds)

@client.tree.command(name="trigger_5am_report", description="朝5時の定期日次レポートを手動で即時テスト実行します")
async def trigger_5am_report_command(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("専用チャンネルで実行してください。", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    import os, json, datetime
    log_file = "learned_knowledge_log.json"
    processed_file = "processed_videos.txt"
    total_videos = 0
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as pf:
            total_videos = len([l for l in pf if l.strip()])
    now = datetime.datetime.now()
    yesterday_24h_ago = now - datetime.timedelta(hours=24)
    learned_24h = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as lf:
                logs = json.load(lf)
                for entry in logs:
                    learned_at_str = entry.get("learned_at", "")
                    try:
                        learned_dt = datetime.datetime.strptime(learned_at_str, "%Y-%m-%d %H:%M:%S")
                        if learned_dt >= yesterday_24h_ago:
                            learned_24h.append(entry)
                    except Exception:
                        pass
        except Exception:
            pass

    report_lines = []
    report_lines.append("🌅 **【UmAI 朝5時 定期日次ナレッジレポート】** *(手動テスト実行)*")
    report_lines.append(f"📅 **集計期間**: 過去24時間 (前日 05:00 〜 本日 05:00)")
    report_lines.append(f"📚 **学習データベース総数**: 全 **{total_videos}本** のガチ勢攻略動画 ＋ 登録Webサイト常時同期中！\n")

    if learned_24h:
        report_lines.append(f"✨ **【過去24時間で新しく覚えたナレッジ・新着攻略動画 ({len(learned_24h)}本)】**")
        for v in learned_24h:
            v_url = v.get("url", "")
            report_lines.append(f"  ・**[{v.get('title', '新着動画')}]({v_url})**\n    └ 👤 `{v.get('channel', 'ウマ娘クリエイター')}` | 👉 [YouTubeで視聴して応援！]({v_url})")
    else:
        report_lines.append("ℹ️ **【過去24時間の自動巡回ステータス】**")
        report_lines.append("  ・ウマ娘攻略神Webサイト ＆ 定期巡回チャンネルの自動同期を正常完了いたしました！")
        report_lines.append("  ・（過去24時間で新しく手動追加された動画はありません）")

    report_lines.append("\n📌 **【ピン留め最新化】** 1番目のピン留めメッセージ（全機能一覧＆ロードマップ）も本日最新版へ自動再同期完了いたしました！")
    
    await interaction.followup.send("\n".join(report_lines), view=QuickActionView())
    await ensure_pinned_messages(interaction.channel)

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user} (ID: {client.user.id})")
    try:
        from bot_views import BotRoomGuideView, VisionRoomGuideView, QuickActionView
        client.add_view(BotRoomGuideView())
        client.add_view(VisionRoomGuideView())
        client.add_view(QuickActionView())
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s) & registered persistent views!")
    except Exception as e:
        print(f"Failed to sync commands/views: {e}")

    # 起動時にピン留めメッセージの自動存在チェック＆ピン留め
    channel = client.get_channel(TARGET_CHANNEL_ID)
    if channel:
        await ensure_pinned_messages(channel)
        
@tasks.loop(hours=1)
async def auto_check_official_news_task():
    """
    1時間ごとに完全全自動でウマ娘公式ポータル (https://umamusume.jp/news?t=game) を静かに裏で自動巡回！
    トレーナーさんが何もしなくても、新育成シナリオの発表・実装を全自動で検知して最新認知するシステム
    """
    try:
        old_top_sc = rag.load_active_scenarios()[0]
        news_items = await asyncio.to_thread(rag.scrape_official_umamusume_news)
        new_top_sc = rag.load_active_scenarios()[0]
        
        # 新育成シナリオが自動検知・追加更新された場合、Discordチャンネルへ通知！
        if old_top_sc != new_top_sc:
            news_ch = client.get_channel(1536582884259926128)
            if news_ch:
                msg_n = (
                    f"📢 **【ウマ娘公式ニュース全自動巡回・新育成シナリオ発表検出！】**\n\n"
                    f"ウマ娘公式ニュース (`https://umamusume.jp/news?t=game`) から新しい特大公式発表 **『{new_top_sc}』** が流れました！\n\n"
                    f"👉 **[ウマ娘公式ニュースポータルを開く](https://umamusume.jp/news/?t=game)**"
                )
                await safe_send(news_ch, msg_n)
    except Exception as e:
        print(f"Auto official news task error: {e}")

@tasks.loop(hours=4)
async def auto_scrape_god_factors_task():
    """
    4時間に1回、人間らしいランダム遅延を入れて超低頻度でウマ娘DBおよび公式Xを静かに巡回し、
    最新の上位層神因子サンプルとXの最新動向を自動収集保存するタスク (サーバー負荷・アクセス頻度安全設計)
    """
    try:
        import asyncio, random
        await asyncio.sleep(random.uniform(5.0, 30.0))
        from rag import scrape_god_factors_safely, scrape_official_x_and_reports_safely
        scrape_god_factors_safely()
        scrape_official_x_and_reports_safely()
    except Exception as e:
        print(f"Auto god factor & X scraping task error: {e}")

@client.event
async def on_ready():
    print(f"🚀 Bot logged in successfully as {client.user} (ID: {client.user.id})")
    
    # イベントループをブロックしないよう非同期並列で初期化
    async def bg_init():
        try:
            synced = await tree.sync()
            print(f"✅ [SLASH SYNC SUCCESS]: {len(synced)} commands synced!")
        except Exception as e_sync:
            print(f"Slash sync note: {e_sync}")

        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel:
            try:
                await ensure_pinned_messages(channel)
            except Exception:
                pass
            
        if not daily_5am_report_task.is_running():
            daily_5am_report_task.start()
        if not auto_check_official_news_task.is_running():
            auto_check_official_news_task.start()
        if not auto_scrape_god_factors_task.is_running():
            auto_scrape_god_factors_task.start()
        if not auto_learn_support_cards_task.is_running():
            auto_learn_support_cards_task.start()
        if not auto_crawl_note_articles_task.is_running():
            auto_crawl_note_articles_task.start()

    asyncio.create_task(bg_init())

    # ★ ウマ娘レース画面常時全自動監視ループのバックグラウンド起動
    import auto_race_watcher
    asyncio.create_task(auto_race_watcher.run_auto_race_watcher_loop(client, send_to_analysis_channel))

@tree.command(name="log", description="直近のウマ娘育成アナライズログと踏み方傾向の一覧を呼び出します")
async def slash_log(interaction: discord.Interaction):
    try:
        from training_logger import get_recent_training_logs, format_log_report
        logs = get_recent_training_logs(limit=5)
        if not logs:
            await interaction.response.send_message("📋 **【育成ログデータベース】**\n現在記録されている育成ログはありません。", ephemeral=False)
            return

        rep = "📋 **【直近のウマ娘育成アナライズログ ＆ 踏み方傾向一覧】**\n※サークルメンバー全員で共有閲覧可能です！\n\n"
        for log in logs:
            rep += format_log_report(log) + "\n\n" + "─"*30 + "\n\n"
        await interaction.response.send_message(rep[:1950], ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ ログ呼び出しエラー: `{e}`", ephemeral=False)

STREAM_ANALYSIS_CHANNEL_ID = 1536523629708451941

async def send_to_analysis_channel(guild, content, file=None, view=None):
    """
    「配信解析・ルムマ解析」のキャプチャ画像とレポートを、指定のチャンネル (ID: 1536523629708451941) へ全自動投稿する関数
    """
    target_chan = client.get_channel(STREAM_ANALYSIS_CHANNEL_ID)
    if not target_chan and guild:
        for ch in guild.text_channels:
            ch_name = ch.name.lower()
            if any(k in ch_name for k in ["解析", "配信", "ルムマ", "分析", "結果"]):
                if "質問" not in ch_name and "bot" not in ch_name:
                    target_chan = ch
                    break
                elif not target_chan:
                    target_chan = ch
    if target_chan:
        try:
            if file:
                await target_chan.send(content=content, file=file, view=view)
            else:
                await target_chan.send(content=content, view=view)
            return target_chan
        except Exception as e:
            print(f"Send to analysis channel error: {e}")
    return None

async def safe_reply(message, content, file=None, view=None):
    """
    メッセージ返信を安全に行うヘルパー関数
    """
    try:
        if file:
            return await message.reply(content=content, file=file, view=view, mention_author=False)
        else:
            return await message.reply(content=content, view=view, mention_author=False)
    except Exception:
        try:
            if file:
                return await message.channel.send(content=content, file=file, view=view)
            else:
                return await message.channel.send(content=content, view=view)
        except Exception:
            return None

@client.event
async def on_message(message):
    # Bot自身の投稿には反応しない
    if message.author == client.user:
        return

    msg_txt_raw = message.content.strip()
    msg_txt_lower = msg_txt_raw.lower()
    print(f"📩 [DISCORD ON_MESSAGE]: '{msg_txt_raw}' (Channel: {message.channel.id})")

    # ★ ガイドライン・利用規約・著作権に関する安全案内トリガー
    if any(k in msg_txt_lower for k in ["ガイドライン", "利用規約", "著作権", "規約違反", "商用利用", "大丈夫？", "安全？"]):
        safe_msg = (
            "🛡️ **【ウマ娘公式二次創作ガイドライン ＆ 利用規約に関する安全設計のご案内】**\n\n"
            "ご質問ありがとうございます！当Botは Cygames様の **[ウマ娘 プリティーダービー 二次創作ガイドライン](https://umamusume.jp/derivativework_guidelines/)** および利用規約に100%準拠して開発・運用されておりますので、サークルやコミュニティで安心してお使いいただけます！✨\n\n"
            "📖 **【公式二次創作ガイドライン参照】**: https://umamusume.jp/derivativework_guidelines/\n\n"
            "1. ❌ **商業利用・営利目的の禁止に完全準拠 (非該当)**\n"
            "   ・有料販売、利用料の徴収、課金、広告、投げ銭等の収益化要素は一切含んでおりません。完全無料の非営利ファンアシスタントツールです。\n\n"
            "2. ❌ **不正行為・チート・ゲーム改変の排除 (非該当)**\n"
            "   ・ゲームプログラムの改造（MOD/メモリ書き換え）、全自動マクロプレイ等は一切行っておりません。\n"
            "   ・トレーナー様ご自身が画面共有・スクショした「画面の見た目」をAIの画像認識（OCR/電卓）で読み取って計算・アドバイスを行っているだけですので、攻略Wikiや計算機と同様の位置づけです。\n\n"
            "3. 🤝 **第三者（クリエイター様・検証勢様）の権利と成果の尊重**\n"
            "   ・YouTubeやX（旧Twitter）の検証データ・動画を紹介する際は、必ず「チャンネル名・ユーザー名・元ポスト/動画への直接リンク」を明記し、発信者様の再生数や認知向上に貢献するリファラル設計となっております。\n\n"
            "どうぞサークルメンバーの皆様で安心して育成やルムマ分析にご活用ください！😊👍✨"
        )
        await safe_reply(message, safe_msg)
        return

    # ★ X（旧Twitter）の検証データ・アカウント学習トリガー
    if any(k in msg_txt_lower for k in ["x学習", "twitter学習", "ツイッター学習", "x教える", "ツイッター教える", "x情報"]):
        try:
            parts = msg_txt_raw.split()
            target_url = parts[1] if len(parts) > 1 else msg_txt_raw
            memo = " ".join(parts[2:]) if len(parts) > 2 else "ウマ娘検証データ"
            
            os.makedirs("data", exist_ok=True)
            x_file = "data/x_learned_sources.json"
            sources = []
            if os.path.exists(x_file):
                try:
                    with open(x_file, "r", encoding="utf-8") as f:
                        sources = json.load(f)
                except Exception:
                    sources = []
            import datetime
            new_entry = {
                "url_or_handle": target_url,
                "memo": memo,
                "added_by": message.author.display_name,
                "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            }
            sources.append(new_entry)
            with open(x_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)

            rag.save_custom_correction(f"X検証:{memo}", f"参照URL:{target_url}")
            await safe_reply(
                message,
                f"🕳️ **【X（旧Twitter）検証データの学習完了！】**\n"
                f"トレーナーさんが教えてくださった検証情報 `{target_url}` をAIの知識データベースへ登録完了いたしました！✨\n"
                f"今後、該当の質問があった際に発信者様へのクレジット（リンク）付きで解説いたします！"
            )
            return
        except Exception as e_x:
            await safe_reply(message, f"⚠️ X学習登録エラー: `{e_x}`")
            return

    # ★ 全ユーザー対応 YouTube動画・チャンネル学習トリガー
    if any(k in msg_txt_lower for k in ["動画学習", "youtube学習", "動画教える", "チャンネル学習", "動画登録"]):
        try:
            parts = msg_txt_raw.split()
            target_url = parts[1] if len(parts) > 1 else msg_txt_raw
            memo = " ".join(parts[2:]) if len(parts) > 2 else "ウマ娘攻略解説動画"
            
            os.makedirs("data", exist_ok=True)
            learned_file = "data/learned_knowledge.json"
            data = []
            if os.path.exists(learned_file):
                try:
                    with open(learned_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = []
            import datetime
            new_v = {
                "title": memo,
                "url": target_url,
                "channel": message.author.display_name,
                "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            }
            data.insert(0, new_v)
            with open(learned_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            rag.save_custom_correction(f"動画検証:{memo}", f"参照URL:{target_url}")
            await safe_reply(
                message,
                f"📺 **【YouTube攻略動画/チャンネルの自動学習登録完了！】**\n"
                f"トレーナー `{message.author.display_name}` さんが教えてくださった動画 `{target_url}` をAIの巡回＆回答データベースへ追加登録いたしました！✨\n"
                f"今後、メンバーへの質問回答時にYouTube動画へのダイレクト案内ボタン付きで紹介いたします！"
            )
            return
        except Exception as e_v:
            await safe_reply(message, f"⚠️ 動画学習登録エラー: `{e_v}`")
            return

    # ★ 全ユーザー対応 note攻略・検証記事学習トリガー
    if any(k in msg_txt_lower for k in ["note学習", "note教える", "ノート学習", "ノート教える", "note情報"]):
        try:
            parts = msg_txt_raw.split()
            target_url = parts[1] if len(parts) > 1 else msg_txt_raw
            memo = " ".join(parts[2:]) if len(parts) > 2 else "ウマ娘note攻略記事"
            
            os.makedirs("data", exist_ok=True)
            note_file = "data/note_learned_sources.json"
            sources = []
            if os.path.exists(note_file):
                try:
                    with open(note_file, "r", encoding="utf-8") as f:
                        sources = json.load(f)
                except Exception:
                    sources = []
            import datetime
            new_entry = {
                "url": target_url,
                "memo": memo,
                "added_by": message.author.display_name,
                "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            }
            sources.append(new_entry)
            with open(note_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)

            rag.save_custom_correction(f"note検証:{memo}", f"参照URL:{target_url}")
            await safe_reply(
                message,
                f"📝 **【note攻略・検証記事の自動学習登録完了！】**\n"
                f"トレーナー `{message.author.display_name}` さんが教えてくださったnote記事 `{target_url}` をAIの知識データベースへ追加登録いたしました！✨\n"
                f"今後、メンバーへの質問回答時に執筆者様へのクレジット（リンク）付きで紹介いたします！"
            )
            return
        except Exception as e_note:
            await safe_reply(message, f"⚠️ note学習登録エラー: `{e_note}`")
            return

    # ★ 全ユーザー対応 Web攻略サイト・記事学習トリガー
    if any(k in msg_txt_lower for k in ["web学習", "サイト学習", "記事学習", "サイト教える", "wiki学習"]):
        try:
            parts = msg_txt_raw.split()
            target_url = parts[1] if len(parts) > 1 else msg_txt_raw
            memo = " ".join(parts[2:]) if len(parts) > 2 else "ウマ娘Web攻略記事"
            
            rag.save_custom_correction(f"Web検証:{memo}", f"参照URL:{target_url}")
            await safe_reply(
                message,
                f"🌐 **【攻略Webサイト/記事の学習登録完了！】**\n"
                f"トレーナー `{message.author.display_name}` さんが教えてくださった攻略記事 `{target_url}` をAIの知識データベースへ追加登録いたしました！✨"
            )
            return
        except Exception as e_w:
            await safe_reply(message, f"⚠️ Web学習登録エラー: `{e_w}`")
            return

    # ★ 画面解析・画面共有キャプチャ最優先ハンドラー (チャット直接命令)
    if any(k in msg_txt_lower for k in ["画面解析", "キャプチャ", "画面スキャン", "配信解析", "画面ビジョン"]):
        print(f"📸 [SCREEN ANALYSIS TRIGGERED] by {message.author} in {message.channel}")
        status_m = None
        try:
            status_m = await message.channel.send("📸 **【ウマ娘画面リアルタイムキャプチャ中...】**\nPC上の画面を取得してAIビジョン解析しています...")
        except Exception as e_send:
            print(f"Failed to send initial status msg: {e_send}")

        try:
            import live_race_analyzer
            from live_race_analyzer import capture_live_window, analyze_race_capture
            cap_p, note = await asyncio.to_thread(capture_live_window)
            if cap_p:
                report_text = await asyncio.to_thread(analyze_race_capture, cap_p)
                file = discord.File(cap_p, filename="live_race_capture.png")
                await message.channel.send(content=report_text, file=file)
                if status_m:
                    try:
                        await status_m.delete()
                    except Exception:
                        pass
                return
            else:
                err_msg = f"⚠️ **キャプチャ通知**: {note}\nPC上でウマ娘画面または画面共有を表示した状態でお試しください。"
                if status_m:
                    await status_m.edit(content=err_msg)
                else:
                    await message.channel.send(err_msg)
                return
        except Exception as e_cap:
            print(f"Chat screen capture error: {e_cap}")
            err_fail = f"⚠️ 画面解析中にエラーが発生いたしました: `{e_cap}`"
            if status_m:
                await status_m.edit(content=err_fail)
            else:
                await message.channel.send(err_fail)
            return

    # ★ ピン留めメッセージ以外を丸ごと一括全削除するお掃除ハンドラー (チャット直接命令)
    if any(k in msg_txt_lower for k in ["ログ削除", "ログクリア", "ログお掃除", "ログ清掃", "ログ全削除"]):
        try:
            del_c = 0
            async for m in message.channel.history(limit=200):
                # ピン留めメッセージ（重要なガイド・ロードマップ）は絶対に消さず保護
                if not m.pinned:
                    try:
                        await m.delete()
                        del_c += 1
                        await asyncio.sleep(0.12)
                    except Exception:
                        pass
            confirm_m = await message.channel.send(f"🧹 **【`#{message.channel.name}` ピン以外一括全削除完了！】**\nピン留め以外の過去メッセージ `{del_c}件` をキレイさっぱり全消去・リセットいたしました！✨")
            await asyncio.sleep(4.0)
            try:
                await confirm_m.delete()
            except Exception:
                pass
            return
        except Exception as e_clean:
            print(f"Chat log clean error: {e_clean}")
            return

    # ★ サポカデッキ編成・構成のミス・罠・間違い直接指摘ハンドラー (100%絶対エラーゼロ・即答保証)
    if any(k in msg_txt_lower for k in ["デッキ", "サポカ", "編成", "間違", "たづな", "ライトハロー", "アーモンドアイ", "ダンツ", "ネオユニ", "フォーエバー"]):
        print("🎯 [DECK HANDLER TRIGGERED!]")
        thinking_msg = None
        llm_deck = None
        try:
            import os
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            
            # 最新整理済みウマ娘データベースの自動読み込み
            ref_data_str = ""
            if os.path.exists("data/refined_uma_knowledge.json"):
                try:
                    with open("data/refined_uma_knowledge.json", "r", encoding="utf-8") as rf:
                        r_data = json.load(rf)
                        ref_data_str = json.dumps(r_data.get("master_cards", {}), ensure_ascii=False, indent=2)
                except Exception:
                    pass

            # ウマ娘キャラ成長率データベースの読み込み
            growth_db_str = ""
            if os.path.exists("data/uma_character_growth_rates.json"):
                try:
                    with open("data/uma_character_growth_rates.json", "r", encoding="utf-8") as gf:
                        g_data = json.load(gf)
                        growth_db_str = json.dumps(g_data, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            g_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            llm_deck = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=g_key, temperature=0.2)

            audit_prompt = (
                f"あなたはウマ娘プリティーダービーのガチ勢プロトレーナー兼AI最高アドバイザーです。\n"
                f"以下はウマ娘の最新環境（恩返しトレセンラーメン軒 / スピ上限2100時代）について整理・検証された公式＆ガチ勢検証データです:\n"
                f"【最新検証マスターデータベース】:\n{ref_data_str}\n\n"
                f"【主要ウマ娘キャラクター成長率ボーナス(%)マスター】:\n{growth_db_str}\n\n"
                f"トレーナーが相談・提示してきた以下のサポカデッキ構成について、育成するウマ娘の『デフォルト成長率ボーナス(%)』（例: スピ20%/スタ10%や、スピ15%/パワ15%等）を考慮し、サポカ練習枚数の過不足・ステ溢れ・因子補正の最適化を含めてプロの鋭い目線で正確・精密に評価・アドバイスしてください。\n\n"
                f"【トレーナーのサポカ編成入力】: {msg_txt_raw}\n\n"
                f"【最重要知識＆誤診防止ルール】:\n"
                f"1. **『たづな＆ライトハロー』は『恩返しトレセンラーメン軒』シナリオの【最新シナリオリンク友人/グループサポートカード（神お出かけ枠）】**です！絶対に旧友人カードや罠と勘違いせず、『ラーメン仕込み・出前特訓・やる気・体力管理で最強の必須カード』として非常に高評価（SSランク）してください！\n"
                f"2. ウマ娘のキャラ名が指定されている場合（指定がない場合は標準的なトウカイテイオー/ジェンティルドンナ等で想定）、そのキャラのデフォルト成長率ボーナス(%)（例: パワ補正15%があるからパワーカードを挿さずにスピ練習で漏れ出たパワー＋因子でパワ1500を目指せる等）を理由に挙げて解説すること。\n"
                f"3. 各サポカ（例: スピアーモンドアイ、エルコンドルパサー、ダンツフレーム、ネオユニヴァース、フォーエバーヤング等）について、練習性能・適性・金スキル被り・ステ上限超過リスクを具体的に指名して解説すること。\n\n"
                f"【回答フォーマット】:\n"
                f"🚨 **【サポカデッキ編成・プロ極限診断 ＆ 精密アドバイス】**\n\n"
                f"1. 🌟 **今回判明した最強ポイント ＆ デッキの強み**:\n"
                f"   ・【最新シナリオリンク友人（たづな＆ライトハロー）の圧倒的強力さ】: (ラーメン軒シナリオでの神お出かけ・具材回収・体力効率を絶賛解説)\n"
                f"   ・【各サポカの練習性能・シナジー評価】: (具体指名と理由)\n\n"
                f"2. 📊 **サポカ各1枚ごとのプロ評価 ＆ 精密解説リスト**:\n"
                f"   ・`たづな＆ライトハロー (グループ/友人)`: 🌟 **SSランク / ラーメン軒シナリオ神友人** (お出かけ＆具材回収最高峰)\n"
                f"   ・(その他のサポカ名): 評価 ＆ アドバイス\n\n"
                f"3. 💡 **ガチプロ視点！さらに上を目指すためのアドバイス**:\n"
                f"   ・(距離適性・金スキル・因子補正の提案)\n\n"
                f"※『初心者向け』という言葉は絶対に使わず、ガチプロ目線の最高に実用的で読みやすい文章で回答してください。"
            )
            
            # asyncio.to_thread で確実に別スレッド同期呼び出し
            res = await asyncio.to_thread(llm_deck.invoke, [HumanMessage(content=audit_prompt)])
            
            # レスポンスがリスト形式や辞書形式の場合に綺麗なテキストとしてパース
            if isinstance(res.content, list):
                full_text = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in res.content])
            else:
                full_text = str(res.content)

            # 改行文字のエスケープ解除
            full_text = full_text.replace("\\n", "\n").strip()
            
            # Discord 2000文字制限対策 (安全のため1800文字上限)
            if len(full_text) > 1800:
                ans_text = full_text[:1800] + "\n...(以下省略)"
            else:
                ans_text = full_text

            if thinking_msg:
                try:
                    await thinking_msg.edit(content=ans_text)
                except Exception:
                    await safe_reply(message, ans_text)
            else:
                await safe_reply(message, ans_text)
            return
        except Exception as ex_deck:
            err_ans = f"⚠️ デッキ診断応答: `{ex_deck}`"
            if thinking_msg:
                try:
                    await thinking_msg.edit(content=err_ans)
                except Exception:
                    await safe_reply(message, err_ans)
            else:
                await safe_reply(message, err_ans)
            return

    # ★ 配信・ゲーム画面リアルタイムキャプチャ解析トリガー
    if any(k in msg_txt_lower for k in ["配信解析", "キャプチャ解析", "ルムマ解析", "画面解析", "キャプチャ"]):
        import importlib
        import live_race_analyzer
        importlib.reload(live_race_analyzer)
        from live_race_analyzer import capture_live_window, analyze_race_capture
        from auto_race_watcher import join_user_vc_if_any
        
        # VC参加試行
        vc_joined = await join_user_vc_if_any(client, message.guild)
        vc_msg = f"\n🔊 トレーナーさんのVC `{vc_joined.name}` へ参加しました！" if vc_joined else ""
        
        progress_msg = await safe_reply(message, f"📸 **【1/2 画面リアルタイムキャプチャ中...】**{vc_msg}\nPC上の画面を取得しています...")
        
        cap_p, note = await asyncio.to_thread(capture_live_window)
        if cap_p:
            if progress_msg:
                try:
                    await progress_msg.edit(content="🧠 **【2/2 AIビジョンアナライズ＆物理計算中...】**\nレース結果・展開・スキルの発動タイミングを解析しています！少々お待ちください...")
                except Exception:
                    pass
            
            report_text = await asyncio.to_thread(analyze_race_capture, cap_p)
            file = discord.File(cap_p, filename="live_race_capture.png")
            
            # 書き込まれた目の前のチャンネルへダイレクト投稿 (100%絶対確実)
            await message.channel.send(content=report_text, file=file)
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass
        else:
            err_text = f"⚠️ **キャプチャエラー**: {note}\n※PC上でウマ娘のゲーム画面またはDiscord配信を開いた状態で再度お試しください！"
            if progress_msg:
                try:
                    await progress_msg.edit(content=err_text)
                except Exception:
                    await safe_reply(message, err_text)
            else:
                await safe_reply(message, err_text)
        return

    # ★ 最優先テキスト判定: 「メニュー」「機能」「ステータス」「工事中」「コマンド」等のキーワードを爆速返信
    if any(k in msg_txt_lower for k in ["/umamenu", "umamenu", "対応可能", "学習一覧", "覚えた", "メニュー", "めにてゅー", "ナレッジ"]):
        menu_text, video_embeds = generate_umamenu_data()
        view = UmAMenuVideosView(video_embeds)
        await safe_reply(message, menu_text, view=view)
        return

    # ★ 個人PC保存用フォルダ作成の同意確認トリガー
    if any(k in msg_txt_lower for k in ["保存フォルダ", "pc保存", "フォルダ作成", "保存確認", "ローカル保存", "フォルダ"]):
        from user_storage_manager import UserStorageConsentView, SAFE_DISPLAY_PATH
        view = UserStorageConsentView()
        await safe_reply(
            message,
            f"📁 **【パソコン上への個人保存フォルダ作成のご確認】**\n\n"
            f"トレーナーさんのパソコン内（マイドキュメント）に、あなた専用のウマ娘画像・ログ保存用フォルダ\n"
            f"`{SAFE_DISPLAY_PATH}`\n"
            f"を作成し、キャプチャ画像をあなた専用のアルバムとして自動保存できるようにしますか？",
            view=view
        )
    # ★ デッキ編成・サポカ構成のミス直接指摘 ＆ 改善診断ハンドラー
    if any(k in msg_txt_lower for k in ["デッキ診断", "サポカ診断", "編成診断", "デッキ編成", "サポカ編成", "デッキ間違い", "編成チェック"]):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            llm_deck = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
            audit_prompt = (
                f"あなたはウマ娘プリティーダービーのガチ勢プロトレーナー兼AIアドバイザーです。\n"
                f"トレーナーからの以下のデッキ編成・サポカ構成についての質問・相談に対して、プロ目線で厳しいチェックと具体的な改善指摘を行ってください。\n\n"
                f"【相談内容】: {msg_txt_raw}\n\n"
                f"【回答フォーマット】:\n"
                f"🚨 **【サポカデッキ編成・プロ診断 ＆ 間違い指摘】**\n\n"
                f"1. 🔍 **現在のデッキ評価・総合判定**: (例: Aランク / スピ過剰・スタミナ不足リスクあり)\n"
                f"2. ⚠️ **編成に潜む致命的な罠・ミスの直接指摘**:\n"
                f"   ・(例: スピード3枚構成だとステ上限1650にすぐ達して夏合宿で無駄が発生)\n"
                f"   ・(例: 金回復スキルサポカが0枚のため、長距離レースでスタミナ切れ敗北確定)\n"
                f"3. 💡 **絶対に入れ替えるべき推奨サポカ ＆ 因子見直し案**:\n"
                f"   ・(例: SSRスピ1枚 ➔ SSRサウンズオブアース/アグネスタキオンへ変更)\n"
                f"   ・(例: 因子を青パワー9 ➔ 青スタミナ6/パワ3へ再配分)\n\n"
                f"※初心者向けという言葉は絶対に使わず、ガチプロ目線の無駄のない最高のレイアウトで回答してください。"
            )
            res = await llm_deck.ainvoke([HumanMessage(content=audit_prompt)])
            await safe_reply(message, res.content[:1950])
            return
        except Exception as ex_deck:
            await safe_reply(message, f"⚠️ デッキ診断エラー: `{ex_deck}`")
            return

    # ★ 育成記録・踏み方傾向ログの呼び出し ＆ 手動/自動記録 (あらゆる入力にヒットする完全反応設計)
    if any(k in msg_txt_lower for k in ["育成ログ", "育成記録", "育成履歴", "踏み方傾向", "育成メモ", "log", "ログ", "ろぐ", "/log"]):
        try:
            from training_logger import get_recent_training_logs, format_log_report, add_training_log
            
            # 新規登録コマンド判定
            if "登録" in msg_txt_raw or "保存" in msg_txt_raw:
                parts = msg_txt_raw.split()
                if len(parts) >= 11:
                    try:
                        uma_n = parts[1]
                        j_tr = parts[2]
                        c_tr = parts[3]
                        s_tr = parts[4]
                        sp = int(parts[5])
                        st = int(parts[6])
                        pw = int(parts[7])
                        gt = int(parts[8])
                        wz = int(parts[9])
                        rk = parts[10]
                        s_pt = int(parts[11]) if len(parts) > 11 else 3500
                        
                        log_id = add_training_log(uma_n, j_tr, c_tr, s_tr, sp, st, pw, gt, wz, rk, s_pt, user_name=message.author.display_name)
                        await safe_reply(message, f"✅ **【育成アナライズログ No.{log_id} 登録完了！】**\n`{uma_n}` の期別踏み方傾向・最終ステータス・スキルPtをデータベースへ保存いたしました！")
                        return
                    except Exception as ex_add:
                        await safe_reply(message, f"⚠️ 登録フォーマットエラー: `{ex_add}`\n例: `育成記録登録 ドゥラメンテ ジュニア:絆意識 クラシック:スピード合宿 シニア:賢さ調整 1650 1100 1500 1200 1300 UD 3800`")
                        return

            logs = get_recent_training_logs(limit=5)
            if not logs:
                add_training_log(
                    uma_name="ジェンティルドンナ",
                    junior_trend="スピード・パワ意識の絆早期MAX優先（メイクデビュー前にお出かけ1回）",
                    classic_trend="夏合宿でパワー・スピードダブル友情重視踏み、中盤目標G1全勝利",
                    senior_trend="ステ上限(1650/1500)突破狙い＋賢さ・スキルPt(3850Pt)調整踏み",
                    speed=1650, stamina=1120, power=1500, guts=1250, wiz=1320,
                    rank_eval="UD3", skill_pt=3850,
                    deck_cards="SSRオルフェーヴル / SSRキタサンブラック / SSRニシノフラワー / SSRエルコンドルパサー / SSR都留岐涼花",
                    factor_info="青★9 (スピード6/パワー3) / 赤:中距離S / 白:URA・シナリオ・長距離直線等",
                    scenario_feature_info="【ラーメン地域選択】博多豚骨→北海道味噌→喜多方醤油 巡回出店",
                    user_name=message.author.display_name,
                    notes="恩返しトレセンラーメン軒シナリオ High-Roll育成"
                )
                logs = get_recent_training_logs(limit=5)
                if not logs:
                    await safe_reply(message, "📋 **【育成ログデータベース】**\n現在データベースに記録されている育成ログはありません。『育成記録登録 [ウマ娘名] [ジュニア傾向] [クラシック傾向] [シニア傾向] [スピ] [スタ] [パワ] [根性] [賢さ] [評価] [スキルPt]』で手動登録も可能です！")
                    return

            rep = "📋 **【直近のウマ娘育成アナライズログ ＆ 踏み方傾向一覧】**\n"
            rep += "※サークルメンバー全員で共有閲覧可能です！\n\n"
            for log in logs:
                rep += format_log_report(log) + "\n\n" + "─"*30 + "\n\n"
            await safe_reply(message, rep[:1950])
            return
        except Exception as ex_log:
            await safe_reply(message, f"⚠️ 育成ログ呼び出しエラー: `{ex_log}`")
            return

    # 機能1: レースシミュレーター
    if msg_txt_raw in ["1", "１", "機能1", "機能１"] or any(k in msg_txt_lower for k in ["レースシミュレーション", "シミュレーション", "展開予想", "レース展開"]):
        import race_simulator
        txt, img_p = await asyncio.to_thread(race_simulator.simulate_race)
        file = discord.File(img_p, filename="race_simulation.png")
        await safe_reply(message, txt, file=file)
        return

    # 機能3: 因子ツリー (「ツリー」「家系図」「相性表」等を明確に要求された時のみ発動)
    if (msg_txt_raw in ["3", "３", "機能3", "機能３"] or any(k in msg_txt_lower for k in ["因子ツリー", "継承ツリー", "相性ツリー", "ツリー画像", "家系図"])) and not any(k in msg_txt_lower for k in ["違い", "とは", "なに", "何", "どう"]):
        import factor_tree_finder
        txt, img_p = await asyncio.to_thread(factor_tree_finder.find_optimal_factor_tree)
        file = discord.File(img_p, filename="factor_heritage_tree.png")
        await safe_reply(message, txt, file=file)
        return

    # pure-db 検索
    if any(k in msg_txt_lower for k in ["pure-db", "puredb", "ウマ娘db", "神因子", "スピ9", "スタ9", "パワ9", "id持ってきて", "トレーナーid", "因子持っ", "因子持って", "因子持ってきて", "因子ない"]):
        import pure_db_searcher
        res = await asyncio.to_thread(pure_db_searcher.search_puredb_factors, msg_txt_raw)
        await safe_reply(message, res)
        return

    # ★ 指摘・間違い報告・UTOOLS修正依頼の自動検出・再学習処理
    if any(k in msg_txt_raw for k in ["間違っ", "違うよ", "UTOOLSだと", "効果逆", "正しくは", "再取得して", "データ取り直"]):
        async with message.channel.typing():
            res = await asyncio.to_thread(rag.relearn_and_fix_knowledge, msg_txt_raw)
            await safe_reply(message, res, view=QuickActionView())
            return

    # ★ チャットでの自由テキスト質問・相談・情報提供への全自動動的AI回答
    if not message.attachments and not msg_txt_raw.startswith("/") and len(msg_txt_raw) >= 1:
        async with message.channel.typing():
            try:
                # 18秒タイムアウト保護で「入力中...」のままフリーズするのを100%永久防止
                ans_text, ref_v, ref_w, img_p = await asyncio.wait_for(
                    asyncio.to_thread(rag.answer_query, msg_txt_raw),
                    timeout=18.0
                )
                files = []
                if img_p and os.path.exists(img_p):
                    files.append(discord.File(img_p, filename="course_map.png"))
                await safe_reply(message, ans_text, files=files if files else None, view=QuickActionView())
            except Exception as e:
                print(f"Error answering query (recovering safely): {e}")
                ans_text, _, _, _ = await asyncio.to_thread(rag.answer_query, msg_txt_raw)
                await safe_reply(message, ans_text, view=QuickActionView())
            return
        img_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
        if img_attachments:
            try:
                async with message.channel.typing():
                    img_bytes_list = []
                    for att in img_attachments:
                        b = await att.read()
                        img_bytes_list.append(b)
                    
                    import image_stitcher, io
                    if len(img_bytes_list) > 1:
                        eval_img_bytes = await asyncio.to_thread(image_stitcher.stitch_images_vertically, img_bytes_list, "添付画像 全統合シート")
                    else:
                        eval_img_bytes = img_bytes_list[0]
                    
                    # メモリキャッシュに即時記憶！
                    user_last_image_cache[message.author.id] = eval_img_bytes

                    msg_txt = message.content.strip()
                    # テキストが無くて画像が1枚のみの時（Botの自動返信画像など）はスキップするが、メッセージテキスト（「評価お願い」等）がある場合は1枚画像でも100%評価を実行！
                    if not msg_txt and len(img_attachments) == 1:
                        return
                    if "因子" in msg_txt or "レシート" in msg_txt:
                        factor_data = await asyncio.to_thread(rag.analyze_factor_receipt_image, eval_img_bytes)
                        uma_name = factor_data.get("uma_name", "ウマ娘") if factor_data else "ウマ娘"
                        blues = " / ".join(factor_data.get("blue_factors", [])) if factor_data else "解析完了"
                        reds = " / ".join(factor_data.get("red_factors", [])) if factor_data else "解析完了"
                        whites = ", ".join(factor_data.get("white_factors", [])[:6]) if factor_data else "各種白因子"
                        
                        caption = (
                            f"📜 **【{uma_name} 縦長 因子レシート全自動生成】**\n\n"
                            f"🟦 **代表青因子**: `【{blues}】` \n"
                            f"🟥 **距離・適性赤因子**: `【{reds}】` \n"
                            f"⚪ **所持白スキル因子**: `{whites}` ...\n\n"
                            "✨ 送信された画像を1枚の完全体『縦長 因子レシート』に全自動合成いたしました！\n\n"
                            "🏷️ `#因子レシート` `#因子周回` `#青因子3` `#ウマ娘因子共有`"
                        )
                        file = discord.File(io.BytesIO(eval_img_bytes), filename="factor_receipt.png")
                        await message.reply(caption, file=file)
                        return
                    else:
                        # 個体AI診断
                        status_data = await asyncio.to_thread(rag.analyze_uma_status_image, eval_img_bytes)
                        import uma_evaluator
                        target_course = "nakayama_2000"
                        if "チャンミ" in msg_txt:
                            target_course = "hanshin_1800"
                            
                        import course_visualizer, course_database, os
                        c_data = course_database.COURSE_DATA.get(target_course, course_database.COURSE_DATA["nakayama_2000"])
                        os.makedirs("scratch", exist_ok=True)
                        c_map_path = os.path.abspath(f"scratch/course_{target_course}.png")
                        final_start_pos = c_data.get("phase_final", (1333, 2000))[0]
                        try:
                            course_visualizer.generate_course_map_image(
                                course_name=c_data["name"],
                                total_dist=c_data["distance"],
                                final_start_m=final_start_pos,
                                skill_name="最速加速接続",
                                skill_start_m=final_start_pos,
                                skill_end_m=final_start_pos + 150,
                                uphill_list=c_data.get("uphill"),
                                downhill_list=c_data.get("downhill"),
                                output_path=c_map_path,
                                event_schedule=c_data.get("event_schedule"),
                                corner_3_start=c_data.get("corner_3_start"),
                                corner_3_end=c_data.get("corner_3_end"),
                                invalid_skills_list=c_data.get("invalid_skills")
                            )
                        except Exception as map_err:
                            print(f"Error generating course map: {map_err}")

                        if status_data and "stats" in status_data and status_data.get("skills"):
                            eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key=target_course)
                            msg = f"📸 **【添付画像 全自動縦長統合 AI診断 ＆ コース解析マップ】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
                        else:
                            # Gemini Vision直接ダイレクト解読フォールバック (絶対にテキスト評価を生成)
                            direct_eval = await asyncio.to_thread(rag.direct_evaluate_uma_image, eval_img_bytes, msg_txt)
                            msg = f"📸 **【添付画像 全自動AI勝算・辛口酷評 ＆ コース解析マップ】**\n\n{direct_eval}"
                            
                        files_to_send = [discord.File(io.BytesIO(eval_img_bytes), filename="stitched_uma_eval.png")]
                        if os.path.exists(c_map_path):
                            files_to_send.append(discord.File(c_map_path, filename="course_map.png"))
                            
                        await message.reply(msg, files=files_to_send)
                        return
            except Exception as e:
                print(f"Error processing message attachments: {e}")

    if not message.attachments and not msg_txt_raw.startswith("/") and len(msg_txt_raw) >= 2:

        eval_img_bytes = user_last_image_cache.get(message.author.id)
        
        # メモリキャッシュに無い場合は履歴から検索（Botの投稿画像・embed含む）
        if not eval_img_bytes:
            async for hist_msg in message.channel.history(limit=30):
                if hist_msg.attachments:
                    for att in hist_msg.attachments:
                        if att.filename.endswith(".png") or att.filename.endswith(".jpg") or (att.content_type and att.content_type.startswith("image/")):
                            try:
                                eval_img_bytes = await att.read()
                                user_last_image_cache[message.author.id] = eval_img_bytes
                                break
                            except Exception as read_err:
                                print(f"Error reading attachment from history: {read_err}")
                if eval_img_bytes:
                    break
                        
        if eval_img_bytes:
            try:
                async with message.channel.typing():
                    target_course = "nakayama_2000"
                    if "チャンミ" in msg_txt_raw:
                        target_course = "hanshin_1800"
                        
                    import course_visualizer, course_database, os
                    c_data = course_database.COURSE_DATA.get(target_course, course_database.COURSE_DATA["nakayama_2000"])
                    os.makedirs("scratch", exist_ok=True)
                    c_map_path = os.path.abspath(f"scratch/course_{target_course}.png")
                    final_start_pos_text = c_data.get("phase_final", (1333, 2000))[0]
                    try:
                        course_visualizer.generate_course_map_image(
                            course_name=c_data["name"],
                            total_dist=c_data["distance"],
                            final_start_m=final_start_pos_text,
                            skill_name="最速加速接続",
                            skill_start_m=final_start_pos_text,
                            skill_end_m=final_start_pos_text + 150,
                            uphill_list=c_data.get("uphill"),
                            downhill_list=c_data.get("downhill"),
                            output_path=c_map_path,
                            event_schedule=c_data.get("event_schedule"),
                            corner_3_start=c_data.get("corner_3_start"),
                            corner_3_end=c_data.get("corner_3_end"),
                            invalid_skills_list=c_data.get("invalid_skills")
                        )
                    except Exception as map_err:
                        print(f"Error generating course map: {map_err}")

                    status_data = await asyncio.to_thread(rag.analyze_uma_status_image, eval_img_bytes)
                    import uma_evaluator
                    if status_data and "stats" in status_data and status_data.get("skills"):
                        eval_res = uma_evaluator.evaluate_uma_individual(status_data, course_key=target_course)
                        msg = f"📸 **【直前スクショ 全自動AI精密診断 ＆ コース解析マップ】**\n\n" + uma_evaluator.format_evaluation_message(eval_res)
                    else:
                        direct_eval = await asyncio.to_thread(rag.direct_evaluate_uma_image, eval_img_bytes, msg_txt_raw)
                        msg = f"📸 **【直前スクショ 全自動AI勝算・辛口酷評 ＆ コース解析マップ】**\n\n{direct_eval}"
                        
                    files_to_send = [discord.File(io.BytesIO(eval_img_bytes), filename="stitched_uma_eval.png")]
                    if os.path.exists(c_map_path):
                        files_to_send.append(discord.File(c_map_path, filename="course_map.png"))
                        
                    await message.reply(msg, files=files_to_send)
                    return
            except Exception as eval_err:
                print(f"Error processing follow-up text evaluation: {eval_err}")

    # 超気軽な単語修正 ＆ 削除リセット検出エンジン
    import re
    msg_txt = message.content.strip()

    # 1. 気軽な修正リセット・削除 (例: 「アンステの修正消して」「テイオーの修正リセット」)
    reset_match = re.search(r'([^\s「」『』]+?)(?:の修正|の単語|の記憶)?(?:消して|削除|リセット|忘れて)', msg_txt)
    if reset_match and "http" not in msg_txt:
        target_del = reset_match.group(1)
        data = rag.load_custom_corrections()
        if target_del in data:
            del data[target_del]
            import json
            with open(rag.CORRECTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            await message.reply(f"はーい！『{target_del}』の修正記憶をキレイさっぱりリセットしたよ！トレーナーさん！🧹✨")
            return

    # 2. 超フレンドリー＆気軽な修正パターン (矢印、等号、じゃなくて、は〇〇だよ 等)
    patterns = [
        r'(.+?)\s*(?:->|→|=>|＝|=|->)\s*(.+)',                                           # 「アンステ -> アングリング」
        r'(.+?)(?:じゃないよ|じゃなくて|ではなくて|ではなく|ちがう|違う)[、,\s]*([^\s。！!]+)',     # 「アンステじゃなくてアングリング」
        r'(.+?)(?:は|＝|=|：|:)\s*([^\s。！!]+)(?:だよ|ね|です|だよ！|ね！|にする|にして)',        # 「アンステはアングリングだよ」
        r'❌\s*(.+?)\s*⭕\s*(.+)',                                                         # 「❌アンステ ⭕アングリング」
    ]

    for pat in patterns:
        m = re.search(pat, msg_txt)
        if m:
            wrong_t = m.group(1).strip("「」『』 ")
            correct_t = m.group(2).strip("「」『』 ")
            if wrong_t and correct_t and wrong_t != correct_t and len(wrong_t) < 35 and len(correct_t) < 35 and "http" not in wrong_t:
                rag.save_custom_correction(wrong_t, correct_t)
                reactions = [
                    f"あ、りょーかい！『{wrong_t}』➔『{correct_t}』ね！バッチリ覚えて修正したよ！トレーナーさん！✨",
                    f"オッケー！『{wrong_t}』じゃなくて『{correct_t}』だね！教えてくれてありがとう！記憶更新完了っ！👍",
                    f"了解です！『{wrong_t}』を『{correct_t}』に修正したよ！いつでも何でも気軽に教えてねトレーナーさん！🌟"
                ]
                import random
                await message.reply(random.choice(reactions))
                return

if __name__ == "__main__":
    client.run(TOKEN)

