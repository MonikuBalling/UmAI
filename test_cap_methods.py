import win32gui
import win32ui
import win32con
from PIL import Image
import os
import mss
from PIL import ImageGrab

print("=== キャプチャ手法実験テスト ===")

# テスト1: PIL ImageGrab
try:
    img = ImageGrab.grab()
    print("1. ImageGrab.grab(): SUCCESS, size=", img.size)
except Exception as e:
    print("1. ImageGrab.grab(): FAILED ->", e)

# テスト2: ImageGrab all_screens
try:
    img = ImageGrab.grab(all_screens=True)
    print("2. ImageGrab.grab(all_screens=True): SUCCESS, size=", img.size)
except Exception as e:
    print("2. ImageGrab.grab(all_screens=True): FAILED ->", e)

# テスト3: win32gui PrintWindow (特定ウィンドウ撮影)
try:
    hwnd = win32gui.FindWindow(None, "UmamusumePrettyDerby_Jpn")
    if not hwnd:
        # discordや他ウィンドウ検索
        def enum_cb(h, extra):
            title = win32gui.GetWindowText(h)
            if "umamusume" in title.lower() or "prettyderby" in title.lower() or "discord" in title.lower():
                extra.append((h, title))
        found = []
        win32gui.EnumWindows(enum_cb, found)
        if found:
            hwnd, title = found[0]
            print(f"ウィンドウ発見: {title} (hwnd={hwnd})")

    if hwnd:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bottom - top
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        
        # PW_RENDERFULLCONTENT = 2
        result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        im.save("test_printwindow.png")
        print("3. PrintWindow(hwnd): SUCCESS, saved test_printwindow.png, result=", result)
    else:
        print("3. PrintWindow(hwnd): 対象ウィンドウが見つかりませんでした。")
except Exception as e:
    print("3. PrintWindow(hwnd): FAILED ->", e)

# テスト4: mss
try:
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[0])
        print("4. mss: SUCCESS, size=", sct_img.size)
except Exception as e:
    print("4. mss: FAILED ->", e)
