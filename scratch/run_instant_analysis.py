import os
import asyncio
import discord
from live_race_analyzer import capture_live_window, analyze_race_capture
from user_storage_manager import save_image_to_user_local

async def main():
    print("📸 [MANUAL RUN] ウマ娘画面のみ限定切抜き撮影中...")
    cap_path, note = capture_live_window()
    if not cap_path:
        print(f"❌ エラー: {note}")
        return

    print(f"✅ キャプチャ成功: {cap_path}")
    print("🧠 Gemini Vision AI + RAG + アルゴリズム解析エンジン実行中...")
    report_text = analyze_race_capture(cap_path)
    
    print("=== 完成したプロアナライズレポート ===")
    print(report_text)
    
    # テキスト出力用にファイル保存
    with open("scratch/last_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

if __name__ == "__main__":
    asyncio.run(main())
