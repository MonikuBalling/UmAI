import os
import subprocess
import sys

# bot.py と同じディレクトリをカレントディレクトリに設定
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

bat_path = os.path.join(base_dir, "run_bot.bat")
subprocess.run([bat_path], shell=True)
