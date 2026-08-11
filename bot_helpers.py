import os
import json
import discord

def generate_umamenu_data():
    """
    /umamenu または 「メニュー」「対応可能」等のキーワードで呼び出される
    習得済み攻略ナレッジ・対応可能アドバイス ＆ 新着学習動画一覧のレスポンスデータを生成する関数
    """
    learned_file = "data/learned_knowledge.json"
    video_titles = []
    if os.path.exists(learned_file):
        try:
            with open(learned_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                video_titles = [v.get("title", "") for v in data if v.get("title")]
        except Exception as e:
            print(f"Error loading learned_knowledge.json: {e}")

    kb_file = "data/uma_knowledge_base.json"
    kb_topics = []
    if os.path.exists(kb_file):
        try:
            with open(kb_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                kb_topics = list(data.keys())
        except Exception as e:
            print(f"Error loading uma_knowledge_base.json: {e}")

    menu_text = (
        "📚 **【ウマ娘AI 習得済み攻略ナレッジ ＆ 対応可能アドバイスメニュー】**\n\n"
        "AIはウマ娘の最新環境（**恩返しトレセンラーメン軒 / スピ上限2100時代**）の全法則・公式データ・ガチ勢検証を完全マスターしております！\n"
        "チャットや `/uma` コマンドで、気になる内容を何でも質問してくださいね！\n\n"
        "📖 **【主な対応可能質問カテゴリ ＆ プロ解析項目】**\n"
        "1. 🏆 **コース立体解析 ＆ 最適スキル** (`中山2000m`, `阪神1800m` の金ピカ第3コーナー・加速接続)\n"
        "2. 🃏 **サポカデッキプロ診断** (キャラ成長率%補正・『たづな＆ライトハロー』リンク評価)\n"
        "3. 📸 **配信・ゲーム画面リアルタイムビジョン解析** (画面共有・スクショから即診断)\n"
        "4. 📜 **1枚絵 縦長因子レシート全自動生成** (代表青3・適性赤・白スキル一覧抽出)\n"
        "5. 🔍 **pure-db 人間偽装神因子検索** (フォロー枠空きあり限定ID自動取得)\n"
        "6. 🏁 **AI 100回モンテカルロ レース展開シミュレーション**\n"
        "7. 🧬 **相性二重丸◎ 最適因子継承ツリー検索**\n\n"
        "✨ 下の動画ボタンをタップすると、AIが自動学習したYouTubeの攻略動画を直接視聴できます！"
    )

    embeds = []
    if os.path.exists(learned_file):
        try:
            with open(learned_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for v in data[:5]:
                    v_url = v.get("url", "https://www.youtube.com")
                    v_title = v.get("title", "ウマ娘最新攻略解説動画")
                    e = discord.Embed(
                        title=f"📺 {v_title}",
                        url=v_url,
                        description=f"👤 **チャンネル**: `{v.get('channel', 'ガチ勢クリエイター')}`\n👉 [YouTubeで動画を直接再生して応援！]({v_url})",
                        color=discord.Color.red()
                    )
                    embeds.append(e)
        except Exception:
            pass

    return menu_text, embeds

def generate_status_roadmap_text():
    return (
        "📊 **【ウマ娘AI システム稼働ステータス ＆ 完全対応ロードマップ】**\n\n"
        "✅ **【現在100%完全稼働中・提供中の神機能一覧 (Active)】**\n"
        "├─ 🤖 **Gemini Flash 最新AI自然会話 ＆ ウマ娘専用ナレッジエンジン**\n"
        "├─ 🃏 **サポカデッキ編成プロ極限診断** (キャラ成長率(%) ＆ 『たづな＆ライトハロー』リンク完全考慮)\n"
        "├─ ✂️ **シームレス縦長画像自動統合** (重複ヘッダー・青枠0ギャップカット)\n"
        "├─ 🌀 **3D/2D 立体コース解析図面生成** (ドーナッツ型 & 金ピカ第3コーナー & 罠スキル警告)\n"
        "├─ 🏆 **全国猛者基準 S+〜C 個体勝算AI診断** (辛口酷評 ＆ 改善アドバイス)\n"
        "├─ 📜 **1枚絵 縦長因子レシート全自動生成** (代表青因子3・赤因子・白スキル一覧切り出し)\n"
        "├─ 🏁 **AIレース展開シミュレーター** (100回モンテカルロ馬身差推移グラフ `/race_sim`)\n"
        "├─ 🧬 **最適因子継承ツリー検索** (相性二重丸◎家系図ツリー算出 `/factor_tree`)\n"
        "├─ 🔍 **pure-db 人間偽装神因子検索** (フォロー枠空きあり限定ID自動取得 `/puredb`)\n"
        "├─ 🎥 **リアルタイム画面キャプチャAI解析** (`/uma_stream_capturer` でPC画面から即診断)\n"
        "├─ 🎴 **所持サポカAI視覚一括登録 DB** (`/register_cards`, `/my_cards` で手持ち＆凸数管理)\n"
        "└─ 📌 **個人メッセージメモ保存機能** (右クリックメニュー / `/mymemo` で閲覧)\n\n"
        "👇 **下の直押しボタンをタップすると、その場で直接機能が起動します！**"
    )

async def refresh_channel_guides_and_pins(client):
    """
    毎日朝5時（および即時実行時）に、2つのDiscordチャンネル
    1. 1396001392581148764 (#質問botの部屋)
    2. 1536523629708451941 (#ウマ娘配信画面分析室)
    の既存のピン留めガイドメッセージを最新内容へedit編集（位置固定・新通知防止）し、ピン留めメッセージを常時維持する全自動関数
    """
    ch_bot = client.get_channel(1396001392581148764)
    ch_vision = client.get_channel(1536523629708451941)
    
    # --- 1. 質問botの部屋 ガイド作成・編集 ---
    if ch_bot:
        try:
            try:
                pins = [m async for m in ch_bot.pins()]
            except Exception:
                pins = await ch_bot.pins()
                
            existing_pin = None
            for p in pins:
                if p.author == client.user and "📌" in (p.embeds[0].title if p.embeds else p.content):
                    existing_pin = p
                    break
            
            embed_bot = discord.Embed(
                title="📌 【ウマ娘AI 攻略質問・育成相談bot部屋 公式ガイド】",
                description="ウマ娘最新環境（**恩返しトレセンラーメン軒 / スピ上限2100時代**）完全対応！\n"
                            "AIがYouTubeガチ勢動画・神因子DB・U-toolsサポカ図鑑と常時全自動同期中！",
                color=discord.Color.green()
            )
            embed_bot.add_field(
                name="🤖 1. AIへの質問・攻略相談",
                value="チャットでウマ娘の疑問を打つだけでAIが最新データから回答！\n(例: `8月のリグヒ用に評価お願い`, `中山2000mのコース図見せて`)",
                inline=False
            )
            embed_bot.add_field(
                name="🃏 2. サポカデッキ編成 ＆ プロ極限診断",
                value="`デッキ間違えている...` や `トウカイテイオーのトレセン軒でのデッキ診断...` と打つと、**ウマ娘のデフォルト成長率(%)**や**最新シナリオリンク神友人『たづな＆ライトハロー』**を考慮してプロ厳しめ評価！",
                inline=False
            )
            embed_bot.add_field(
                name="🧹 3. お部屋のログ一括全削除・リセット",
                value="`ログ削除` や `ログクリア` と打つだけで、ピン留めメッセージ以外をキレイに全消去・リセット！",
                inline=False
            )
            embed_bot.add_field(
                name="📜 4. 使える全コマンド一覧マニュアル",
                value="・`/uma [質問]` : 最新環境・コース図面・物理公式質問\n"
                      "・`/log` (チャット `育成ログ`) : 直近の育成アナライズ全出力\n"
                      "・`/logclean` (チャット `ログ削除`) : ピン留め以外の部屋ログ一括全消去\n"
                      "・`/puredb [条件]` : フォロー枠空きあり神因子ID自動検索\n"
                      "・`/race_sim` : AI 100回モンテカルロ レース展開シミュレーター\n"
                      "・`/factor_tree` : 相性二重丸◎ 最適因子継承ツリー検索",
                inline=False
            )
            embed_bot.add_field(
                name="⚡ 5. 定期全自動機能",
                value="・毎日朝5時に最新ガイドメッセージへ全自動内容再更新（メッセージ位置は固定）\n・6時間ごとのサポカ図鑑＆YouTube動画全自動巡回学習",
                inline=False
            )
            embed_bot.set_footer(text="ウマ娘AI 攻略アシスタントBot (毎日朝5時自動更新)")
            
            from bot_views import BotRoomGuideView
            if existing_pin:
                await existing_pin.edit(embed=embed_bot, view=BotRoomGuideView())
                print("✅ [#質問botの部屋] 既存ピン留めガイドの内容再更新完了！")
            else:
                new_msg_bot = await ch_bot.send(embed=embed_bot, view=BotRoomGuideView())
                await new_msg_bot.pin()
                print("✅ [#質問botの部屋] 新ガイド作成・ピン留め完了！")
        except Exception as e1:
            print(f"Refresh bot room guide error: {e1}")

    # --- 2. ウマ娘配信画面分析室 ガイド作成・編集 ---
    if ch_vision:
        try:
            try:
                pins_v = [m async for m in ch_vision.pins()]
            except Exception:
                pins_v = await ch_vision.pins()

            existing_pin_v = None
            for p in pins_v:
                if p.author == client.user and "📌" in (p.embeds[0].title if p.embeds else p.content):
                    existing_pin_v = p
                    break

            embed_v = discord.Embed(
                title="📌 【ウマ娘AI 配信画面・キャプチャリアルタイム分析室 公式ガイド】",
                description="ウマ娘の画面（レース結果・育成完了ステータス・サポカ編成画面）をAIビジョンがリアルタイムで物理・画像解析！",
                color=discord.Color.purple()
            )
            embed_v.add_field(
                name="📸 1. リアルタイム画面キャプチャ解析",
                value="チャットで `画面解析`, `キャプチャ`, `配信解析` と打つだけで、PC上の目の前のウマ娘画面を取得してビジョン解析！",
                inline=False
            )
            embed_v.add_field(
                name="🔊 2. Discord VC自動参加 ＆ 音声フィードバック",
                value="VC参加中に `画面解析` と打つと、BotがVCに自動参加してプロアナライズを音声＆テキストでフィードバック！",
                inline=False
            )
            embed_v.add_field(
                name="🃏 3. U-toolsサポカ図鑑照合 ＆ 得意率/友情倍率自動計算",
                value="サポカ編成画面から6枚の絵柄を認識し、**得意率合計(例: 380)** や **友情爆発倍率(例: x3.45)** を自動数値算出！",
                inline=False
            )
            embed_v.add_field(
                name="📊 4. 期別トレ踏み方 ＆ 5次元アルゴリズム分析",
                value="ジュニア〜シニア期の踏み方、トレーナー属性タイプ分類（例: 🧠 スキルPt最大化賢さ頭脳派型）を全自動分析！",
                inline=False
            )
            embed_v.add_field(
                name="🧹 5. お部屋のログ全削除",
                value="チャットで `ログ削除` と打つと、ピン留めメッセージを残して部屋のログを一瞬でリセット！",
                inline=False
            )
            embed_v.add_field(
                name="📜 6. 使える全コマンド一覧マニュアル",
                value="・チャット `画面解析` / `/uma_stream_capturer` : 画面ビジョンリアルタイム解析\n"
                      "・チャット `ログ削除` / `/logclean` : ピン留め以外の部屋ログ一括全消去\n"
                      "・`/register_cards` : 所持サポカ一覧画像からAI視覚自動登録\n"
                      "・`/my_cards` : 自分の手持ち所持サポカ・凸数一覧表示",
                inline=False
            )
            embed_v.set_footer(text="ウマ娘AI ビジョンアナライザーBot (毎日朝5時自動更新)")

            from bot_views import VisionRoomGuideView
            if existing_pin_v:
                await existing_pin_v.edit(embed=embed_v, view=VisionRoomGuideView())
                print("✅ [#ウマ娘配信画面分析室] 既存ピン留めガイドの内容再更新完了！")
            else:
                new_msg_v = await ch_vision.send(embed=embed_v, view=VisionRoomGuideView())
                await new_msg_v.pin()
                print("✅ [#ウマ娘配信画面分析室] 新ガイド作成・ピン留め完了！")
        except Exception as e2:
            print(f"Refresh vision room guide error: {e2}")
