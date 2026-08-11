import os
import json
import discord
import asyncio

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
        import rag
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
        import pure_db_searcher
        res = await asyncio.to_thread(pure_db_searcher.search_puredb_factors, cond)
        await interaction.followup.send(res)

class QuickActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔍 pure-db 神因子ID検索", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="quick_btn_puredb")
    async def btn_puredb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PureDbSearchModal())

    @discord.ui.button(label="🏁 AIレース展開シミュレーター", style=discord.ButtonStyle.danger, emoji="🏁", custom_id="quick_btn_race_sim")
    async def btn_race_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import race_simulator
        txt, img_p = await asyncio.to_thread(race_simulator.simulate_race)
        file = discord.File(img_p, filename="race_simulation.png")
        await interaction.followup.send(txt, file=file)

    @discord.ui.button(label="🧬 最適因子継承ツリー検索", style=discord.ButtonStyle.success, emoji="🧬", custom_id="quick_btn_factor_tree")
    async def btn_factor_tree(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import factor_tree_finder
        txt, img_p = await asyncio.to_thread(factor_tree_finder.find_optimal_factor_tree)
        file = discord.File(img_p, filename="factor_heritage_tree.png")
        await interaction.followup.send(txt, file=file)

    @discord.ui.button(label="💬 AIに質問・コース計算", style=discord.ButtonStyle.secondary, emoji="❓", custom_id="quick_btn_question")
    async def btn_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UmaQuestionModal())

    @discord.ui.button(label="📚 対応ナレッジメニュー", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="quick_btn_menu")
    async def btn_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        import bot_helpers
        menu_text, video_embeds = bot_helpers.generate_umamenu_data()
        view = UmAMenuVideosView(video_embeds)
        await interaction.followup.send(menu_text, view=view)

class DeckAuditModal(discord.ui.Modal, title="ウマ娘AI サポカデッキプロ極限診断"):
    uma_input = discord.ui.TextInput(
        label="育成ウマ娘（例: トウカイテイオー / ジェンティルドンナ）",
        style=discord.TextStyle.short,
        placeholder="例: トウカイテイオー",
        required=False,
        default="トウカイテイオー"
    )
    deck_input = discord.ui.TextInput(
        label="サポカ6枚の編成（例: たづな＆ライトハロー, スピアーモンドアイ...）",
        style=discord.TextStyle.paragraph,
        placeholder="例: 友人たづな&ライトハロー、スピードアーモンドアイ、スピードエルコンドルパサー...",
        required=True,
        max_length=400
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        uma = self.uma_input.value or "トウカイテイオー"
        deck = self.deck_input.value
        prompt_txt = f"{uma}の、トレセン軒でのデッキ診断。{deck}"
        
        try:
            import os
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            
            ref_data_str = ""
            if os.path.exists("data/refined_uma_knowledge.json"):
                try:
                    with open("data/refined_uma_knowledge.json", "r", encoding="utf-8") as rf:
                        ref_data_str = json.dumps(json.load(rf).get("master_cards", {}), ensure_ascii=False, indent=2)
                except Exception:
                    pass
            growth_db_str = ""
            if os.path.exists("data/uma_character_growth_rates.json"):
                try:
                    with open("data/uma_character_growth_rates.json", "r", encoding="utf-8") as gf:
                        growth_db_str = json.dumps(json.load(gf), ensure_ascii=False, indent=2)
                except Exception:
                    pass

            g_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=g_key, temperature=0.2)
            audit_prompt = (
                f"あなたはウマ娘のガチ勢プロアドバイザーです。\n"
                f"【最新検証マスターデータベース】:\n{ref_data_str}\n\n"
                f"【主要キャラ成長率ボーナス(%)マスター】:\n{growth_db_str}\n\n"
                f"入力されたウマ娘({uma})の『成長率ボーナス(%)』と、最新シナリオリンク神友人『たづな＆ライトハロー』の恩恵を考慮し、以下のデッキ編成を厳しめプロ評価してください:\n"
                f"【入力編成】: {prompt_txt}\n"
            )
            res = await asyncio.to_thread(llm.invoke, [HumanMessage(content=audit_prompt)])
            txt = str(res.content).replace("\\n", "\n").strip()
            if len(txt) > 1800:
                txt = txt[:1800] + "\n...(以下省略)"
            await interaction.followup.send(txt)
        except Exception as e:
            await interaction.followup.send(f"⚠️ 診断エラー: {e}")

class BotRoomGuideView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💬 AIに質問・コース計算", style=discord.ButtonStyle.primary, emoji="💬", custom_id="bot_guide_btn_q")
    async def btn_q(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UmaQuestionModal())

    @discord.ui.button(label="🃏 サポカデッキプロ診断", style=discord.ButtonStyle.success, emoji="🃏", custom_id="bot_guide_btn_deck")
    async def btn_deck(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeckAuditModal())

    @discord.ui.button(label="🧹 この部屋のログ一括全削除", style=discord.ButtonStyle.danger, emoji="🧹", custom_id="bot_guide_btn_clean")
    async def btn_clean(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        try:
            deleted = await interaction.channel.purge(limit=200, check=lambda m: not m.pinned)
            del_c = len(deleted)
        except Exception:
            del_c = 0
            async for m in interaction.channel.history(limit=200):
                if not m.pinned:
                    try:
                        await m.delete()
                        del_c += 1
                    except Exception:
                        pass
        await interaction.followup.send(f"🧹 **ピン留め以外の過去ログ `{del_c}件` を一瞬で全削除いたしました！**", ephemeral=True)

    @discord.ui.button(label="🔍 pure-db 神因子検索", style=discord.ButtonStyle.secondary, emoji="🔍", custom_id="bot_guide_btn_pure")
    async def btn_pure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PureDbSearchModal())

class VisionRoomGuideView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📸 今すぐ画面キャプチャリアルタイム解析", style=discord.ButtonStyle.primary, emoji="📸", custom_id="vision_guide_btn_cap")
    async def btn_cap(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=False)
            except Exception:
                pass
        import live_race_analyzer
        from live_race_analyzer import capture_live_window, analyze_race_capture
        progress_m = await interaction.followup.send("📸 **【画面リアルタイムキャプチャ中...】**\nPC上の画面を取得してビジョン解析しています...")
        cap_p, note = await asyncio.to_thread(capture_live_window)
        if cap_p:
            report_text = await asyncio.to_thread(analyze_race_capture, cap_p)
            file = discord.File(cap_p, filename="live_race_capture.png")
            await interaction.channel.send(content=report_text, file=file)
            try:
                await progress_m.delete()
            except Exception:
                pass
        else:
            await progress_m.edit(content=f"⚠️ **キャプチャエラー**: {note}\nPC上でウマ娘画面を開いた状態でお試しください。")

    @discord.ui.button(label="🧹 この部屋のログ一括全削除", style=discord.ButtonStyle.danger, emoji="🧹", custom_id="vision_guide_btn_clean")
    async def btn_clean(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        try:
            deleted = await interaction.channel.purge(limit=200, check=lambda m: not m.pinned)
            del_c = len(deleted)
        except Exception:
            del_c = 0
            async for m in interaction.channel.history(limit=200):
                if not m.pinned:
                    try:
                        await m.delete()
                        del_c += 1
                    except Exception:
                        pass
        await interaction.followup.send(f"🧹 **ピン留め以外の過去ログ `{del_c}件` を一瞬で全削除いたしました！**", ephemeral=True)
