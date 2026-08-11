import pyautogui
from PIL import Image

print("=== PyAutoGUI Screenshot Test ===")
try:
    img = pyautogui.screenshot()
    img.save("test_pyautogui_success.png")
    print("✅ PyAutoGUI screenshot 100% SUCCESS! Saved image size:", img.size)
except Exception as e:
    print("❌ PyAutoGUI screenshot FAILED:", e)
