from live_race_analyzer import capture_live_window

print("=== ウマ娘ゲーム画面のみピンポイント切抜き撮影テスト ===")
path, note = capture_live_window()
print(f"結果: path={path}, note={note}")
