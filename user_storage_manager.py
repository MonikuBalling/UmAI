import os
import sqlite3
import discord
import shutil
from datetime import datetime

# ユーザーごとの個人保存フォルダ基準パス (マイドキュメント内)
DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
DEFAULT_USER_LOG_DIR = os.path.join(DOCUMENTS_DIR, "UmAI_Training_Logs")
# 本名/ユーザー名を隠した表示用マスクパス
SAFE_DISPLAY_PATH = "マイドキュメント\\UmAI_Training_Logs"

USER_PREF_DB = os.path.join(os.path.dirname(__file__), "data", "user_preferences.db")

def init_pref_db():
    """ユーザー個人保存設定用DB初期化"""
    os.makedirs(os.path.dirname(USER_PREF_DB), exist_ok=True)
    conn = sqlite3.connect(USER_PREF_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            user_id TEXT PRIMARY KEY,
            storage_consent INTEGER DEFAULT 0,
            custom_folder_path TEXT
        )
    """)
    conn.commit()
    conn.close()

init_pref_db()

def get_user_consent(user_id):
    """ユーザーの保存同意状態を取得 (0: 未確認/拒否, 1: 同意済み)"""
    conn = sqlite3.connect(USER_PREF_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT storage_consent, custom_folder_path FROM user_prefs WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1] or DEFAULT_USER_LOG_DIR
    return 0, DEFAULT_USER_LOG_DIR

def set_user_consent(user_id, consent=1, custom_path=None):
    """ユーザーの保存同意状態を更新し、フォルダを自動生成"""
    folder_path = custom_path or DEFAULT_USER_LOG_DIR
    if consent == 1:
        os.makedirs(folder_path, exist_ok=True)
        os.makedirs(os.path.join(folder_path, "レース結果画像"), exist_ok=True)
        os.makedirs(os.path.join(folder_path, "育成完了ステータス画像"), exist_ok=True)
        
    conn = sqlite3.connect(USER_PREF_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_prefs (user_id, storage_consent, custom_folder_path)
        VALUES (?, ?, ?)
    """, (str(user_id), consent, folder_path))
    conn.commit()
    conn.close()
    return SAFE_DISPLAY_PATH

def save_image_to_user_local(user_id, src_image_path, is_training_summary=False):
    """同意済みの各トレーナーの場合、そのトレーナー自身のローカルPCマイドキュメントへ画像を個別保存"""
    consent, folder_path = get_user_consent(user_id)
    if consent != 1:
        return None
    
    sub_folder = "育成完了ステータス画像" if is_training_summary else "レース結果画像"
    target_dir = os.path.join(folder_path, sub_folder)
    os.makedirs(target_dir, exist_ok=True)
    
    file_name = f"umamusume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    dest_path = os.path.join(target_dir, file_name)
    try:
        shutil.copy(src_image_path, dest_path)
        print(f"✅ [LOCAL MULTI-SAVE SUCCESS]: {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Local save note: {e}")
        return None

class UserStorageConsentView(discord.ui.View):
    """パソコン上への個人保存フォルダ作成同意確認UI View"""
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="はい (パソコン上に専用保存フォルダを作成)", style=discord.ButtonStyle.green, emoji="📁")
    async def consent_yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_user_consent(interaction.user.id, consent=1)
        await interaction.response.send_message(
            f"✅ **【パソコン上の保存フォルダ作成が完了いたしました！】**\n\n"
            f"📁 **保存先**: `{SAFE_DISPLAY_PATH}`\n"
            f"今後、キャプチャされたウマ娘のゲーム画像がこちらのローカルフォルダへあなた専用のアルバムとして自動保存・蓄積されます！",
            ephemeral=True
        )

    @discord.ui.button(label="いいえ (ローカル保存なしで利用)", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def consent_no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_user_consent(interaction.user.id, consent=0)
        await interaction.response.send_message(
            "👌 **【了解いたしました】**\nパソコン上への画像保存を行わずに通常通りご利用いただけます。",
            ephemeral=True
        )
