from dotenv import load_dotenv
load_dotenv()
from live_race_analyzer import analyze_race_capture

img_path = r"C:\Users\`ken\.gemini\antigravity\brain\0bec0171-9827-45ca-8d9c-40d2ac3ccf5d\.user_uploaded\media_1786407923904.png"
res = analyze_race_capture(img_path)
with open("ai_result.txt", "w", encoding="utf-8") as f:
    f.write(res)
print("SUCCESS! Output written to ai_result.txt")
