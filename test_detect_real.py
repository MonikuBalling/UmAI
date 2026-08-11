import cv2
import numpy as np
from PIL import Image

img_path = r"C:\Users\`ken\.gemini\antigravity\brain\0bec0171-9827-45ca-8d9c-40d2ac3ccf5d\.user_uploaded\media_1786407923904.png"
pil_img = Image.open(img_path)

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

print(f"実画面テスト結果:")
print(f"・緑ピクセル数(次へボタン等): {green_pixels}")
print(f"・黄ピクセル数(着順リボン等): {yellow_pixels}")
print(f"・画面全体解像度: {cv_img.shape[1]}x{cv_img.shape[0]}")
