import dxcam
from PIL import Image

print("=== DXCam (DirectX Desktop Duplication API) 撮影テスト ===")
try:
    camera = dxcam.create()
    frame = camera.grab()
    if frame is not None:
        img = Image.fromarray(frame)
        img.save("test_dxcam_success.png")
        print("✅ DXCam キャプチャ100%成功！ 保存画像サイズ:", img.size)
    else:
        print("⚠️ DXCam: フレームがNoneでした。1度スリープを入れて再試行します...")
        import time
        time.sleep(0.5)
        frame = camera.grab()
        if frame is not None:
            img = Image.fromarray(frame)
            img.save("test_dxcam_success.png")
            print("✅ DXCam キャプチャ100%成功！ 保存画像サイズ:", img.size)
        else:
            print("❌ DXCam: 再試行もフレーム取得不可でした。")
except Exception as e:
    print("❌ DXCam エラー:", e)
