import pygetwindow as gw
import mss
import os

print("--- PC上で検出されたウィンドウ一覧 ---")
titles = gw.getAllTitles()
for t in titles:
    if t.strip():
        print(f"・{t}")

print("\n--- キャプチャテスト実行 ---")
from live_race_analyzer import capture_live_window
path, note = capture_live_window()
print(f"結果: path={path}, note={note}")
