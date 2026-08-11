from live_race_analyzer import capture_live_window
from PIL import Image
import os

print("=== 100%ウマ娘画面限定クロップ動作検証 ===")
cap_p, note = capture_live_window()
print(f"結果: path={cap_p}, note={note}")
if cap_p and os.path.exists(cap_p):
    img = Image.open(cap_p)
    print(f"✅ 切り抜かれた画像サイズ: {img.size}")
