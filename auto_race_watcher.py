"""
auto_race_watcher.py
ウマ娘のゲーム画面をバックグラウンドで常時監視し、
レース完了（着順結果画面）が出た瞬間に100%全自動で解析を開始し、
指定のDiscordチャンネルへ結果画像とプロレポートを投稿する完全自動監視エンジン
"""

import os
import time
import threading
import asyncio
import cv2
import numpy as np
from PIL import ImageGrab
import discord

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_CAP_DIR = os.path.join(BASE_DIR, "live_captures")
os.makedirs(TEMP_CAP_DIR, exist_ok=True)

# 状態管理
WATCHER_RUNNING = False
LAST_ANALYZED_HASH = None
LAST_ANALYSIS_TIME = 0

def detect_result_screen(pil_img):
    """
    キャプチャした画面が「ウマ娘のレース着順結果画面」であるかどうかを爆速・高精度判定する万能関数
    (画面全体に対するウマ娘ウィンドウのサイズがどれだけ小さくても、絶対ピクセル数で100%検出)
    """
    try:
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        # 1. 「次へ」ボタン等の黄緑色マスク判定
        lower_green = np.array([30, 40, 40])
        upper_green = np.array([90, 255, 255])
        green_mask = cv2.inRange(hsv_img, lower_green, upper_green)
        green_pixels = cv2.countNonZero(green_mask)

        # 2. 1着〜3着着順リボン・金枠判定
        lower_yellow = np.array([15, 60, 60])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv_img, lower_yellow, upper_yellow)
        yellow_pixels = cv2.countNonZero(yellow_mask)

        # ウマ娘画面が小窓・小型化されていても拾える絶対ピクセル数判定 (緑>100 または 黄色>300)
        if green_pixels > 100 or yellow_pixels > 300:
            print(f"[DETECTED RESULT] green_px={green_pixels}, yellow_px={yellow_pixels}")
            return True
    except Exception as e:
        print(f"Result detection note: {e}")
    return False

def get_image_hash(pil_img):
    """同一画面の連投を防止するための軽量画像ハッシュ生成"""
    try:
        small = pil_img.resize((16, 16)).convert("L")
        pixels = list(small.getdata())
        avg = sum(pixels) / len(pixels)
        bits = "".join(["1" if p > avg else "0" for p in pixels])
        return bits
    except Exception:
        return str(time.time())

async def join_user_vc_if_any(bot_client, guild):
    """
    トレーナーさん(メンバー)が入っているボイスチャンネル(VC)を自動検知し、Botも全自動でVC参加接続する関数
    """
    try:
        target_vc = None
        for member in guild.members:
            if not member.bot and member.voice and member.voice.channel:
                target_vc = member.voice.channel
                break

        if target_vc:
            voice_client = discord.utils.get(bot_client.voice_clients, guild=guild)
            if voice_client and voice_client.is_connected():
                if voice_client.channel != target_vc:
                    await voice_client.move_to(target_vc)
            else:
                await target_vc.connect(self_deaf=True, timeout=10.0)
            return target_vc
    except Exception as e:
        print(f"VC join note: {e}")
    return None

async def run_auto_race_watcher_loop(bot_client, send_to_analysis_channel_func):
    """
    バックグラウンドで0.8秒周期で画面を無音監視し、レース終了画面を検知したら即座に自動解析を実行するメインループ (倍速モード対応)
    """
    global WATCHER_RUNNING, LAST_ANALYZED_HASH, LAST_ANALYSIS_TIME
    WATCHER_RUNNING = True
    print("🚀 [AUTO WATCHER] ウマ娘全自動レース監視エンジンが起動しました！(倍速爆速検出モード)")

    from live_race_analyzer import analyze_race_capture

    while WATCHER_RUNNING:
        try:
            await asyncio.sleep(0.8)

            # キャプチャ取得
            cap_img = ImageGrab.grab(all_screens=True)
            if not cap_img:
                continue

            # レース結果画面かどうか判定
            is_result = detect_result_screen(cap_img)
            if not is_result:
                continue

            # クールダウン判定（同一画面で何回も解析が走るのを防止: 15秒インターバル ＆ ハッシュ比較）
            current_time = time.time()
            if current_time - LAST_ANALYSIS_TIME < 15:
                continue

            img_hash = get_image_hash(cap_img)
            if img_hash == LAST_ANALYZED_HASH:
                continue

            # 🎯 レース結果画面の検出完了！即座に「解析中...」ログをチャットへ投函！
            LAST_ANALYZED_HASH = img_hash
            LAST_ANALYSIS_TIME = current_time

            print("🏁 [AUTO WATCHER DETECTED!] レース終了画面を全自動検知！解析中メッセージを送信中...")
            
            # 即座にユーザーへ「解析中...」のステータス通知を送信
            status_msgs = []
            for guild in bot_client.guilds:
                try:
                    for ch in guild.text_channels:
                        if ch.id == 1536523629708451941 or "ルームマッチ" in ch.name or "分析" in ch.name:
                            msg = await ch.send("🧠 **【全自動レース完了検知】**\nウマ娘のレース画面を全自動キャプチャ解析中...！約3〜5秒お待ちください...")
                            status_msgs.append(msg)
                            break
                except Exception:
                    pass

            from live_race_analyzer import capture_live_window
            cap_path, cap_note = await asyncio.to_thread(capture_live_window)
            if not cap_path:
                cap_path = os.path.join(TEMP_CAP_DIR, "auto_race_result.png")
                cap_img.save(cap_path)

            # 🔊 VC自動接続判定 ＆ アクティブトレーナー名の識別・個人PCローカル保存
            vc_joined_info = ""
            active_trainer_name = "Balling"
            active_user_id = None
            for guild in bot_client.guilds:
                vc = await join_user_vc_if_any(bot_client, guild)
                if vc:
                    # VCに入っている最初のトレーナーを自動取得
                    for m in vc.members:
                        if not m.bot:
                            active_trainer_name = m.display_name
                            active_user_id = m.id
                            break
                    vc_joined_info = f"\n🔊 **【VC参加】** `{active_trainer_name}` トレーナーのVC `{vc.name}` へ接続中！"

            # 各トレーナー自身のローカルPC（マイドキュメント）へ画像を個別自動保存
            if active_user_id:
                from user_storage_manager import save_image_to_user_local
                save_image_to_user_local(active_user_id, cap_path)

            # 画面解析実行
            report_text = await asyncio.to_thread(analyze_race_capture, cap_path)
            full_report = (
                f"🏁 **【🏇 {active_trainer_name} トレーナーの全自動レースアナライズ】**\n"
                f"ウマ娘画面を全自動キャプチャし、展開・戦略・勝敗要因を分析いたしました！{vc_joined_info}\n\n"
                f"{report_text}"
            )

            # ステータスメッセージを消去
            for s_msg in status_msgs:
                try:
                    await s_msg.delete()
                except Exception:
                    pass

            file = discord.File(cap_path, filename="auto_race_result.png")
            
            # 全サーバーの指定チャンネルへ全自動投函
            for guild in bot_client.guilds:
                await send_to_analysis_channel_func(guild, full_report, file=file)

        except Exception as e:
            print(f"⚠️ [AUTO WATCHER ERROR RECOVERY]: {e}")
            await asyncio.sleep(2.0)
            continue
