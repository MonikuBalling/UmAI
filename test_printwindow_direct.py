import os
from live_race_analyzer import capture_live_window

print("=== win32gui PrintWindow 直球キャプチャテスト ===")
path, note = capture_live_window()
print(f"結果: path={path}, note={note}")
