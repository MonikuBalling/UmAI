import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from live_race_analyzer import capture_live_window, analyze_race_capture

cap_path, note = capture_live_window()
print(f"Cap path: {cap_path}, Note: {note}")

if cap_path and os.path.exists(cap_path):
    report_text = analyze_race_capture(cap_path)
    with open("scratch/last_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("SUCCESS: Report saved to scratch/last_report.txt")
else:
    print("NO_CAP_FOUND")
