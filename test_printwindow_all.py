import win32gui
import win32ui
from PIL import Image

found_windows = []

def enum_windows_callback(hwnd, extra):
    if not win32gui.IsWindowVisible(hwnd):
        return
    title = win32gui.GetWindowText(hwnd)
    if not title or not title.strip():
        return
    rect = win32gui.GetWindowRect(hwnd)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    if w > 100 and h > 100:
        found_windows.append((hwnd, title, w, h))

win32gui.EnumWindows(enum_windows_callback, None)

print(f"Total visible windows found: {len(found_windows)}")
target_hwnd = None
target_title = ""
target_w = 0
target_h = 0

for hwnd, title, w, h in found_windows:
    print(f"HWND {hwnd} | Size {w}x{h} | Title: {title}")
    t_lower = title.lower()
    if any(k in t_lower for k in ["uma", "pretty", "derby", "ウマ", "discord", "黒の民"]):
        if not target_hwnd:
            target_hwnd = hwnd
            target_title = title
            target_w = w
            target_h = h

if target_hwnd:
    print(f"\nTarget Window Found: [HWND {target_hwnd}] {target_title} ({target_w}x{target_h})")
    hwndDC = win32gui.GetWindowDC(target_hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, target_w, target_h)
    saveDC.SelectObject(saveBitMap)
    
    result = win32gui.PrintWindow(target_hwnd, saveDC.GetSafeHdc(), 2)
    
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    
    im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(target_hwnd, hwndDC)
    
    im.save("test_printwindow_success.png")
    print(f"SUCCESS! Saved test_printwindow_success.png with size {im.size}")
else:
    print("No matching target window found.")
