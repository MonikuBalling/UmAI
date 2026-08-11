from PIL import Image
import os

# 送信された画像から「ウマ娘ゲーム画面」領域のみを100%ピンポイントクロップ
raw_img_path = r"C:\Users\`ken\.gemini\antigravity\brain\0bec0171-9827-45ca-8d9c-40d2ac3ccf5d\.user_uploaded\media_1786407923904.png"
img = Image.open(raw_img_path)

# ウマ娘のゲーム画面は右下の 1024x576 領域にある
# 全体解像度 1920x1080
w, h = img.size

# 右下のウマ娘ウィンドウ領域を厳密切抜き
crop_box = (w - 1035, h - 600, w, h)
pure_uma_img = img.crop(crop_box)

out_path = r"C:\Users\`ken\OneDrive\Desktop\UMAMUSUME便利アプリ開発用Project\YOUTUBE_AI\pure_umamusume_only.png"
pure_uma_img.save(out_path)

print(f"✅ SUCCESS: Cropped pure Umamusume image saved to {out_path} (Size: {pure_uma_img.size})")
