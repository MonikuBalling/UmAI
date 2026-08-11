@echo off
chcp 65001 >nul
cd /d "%~dp0"

:loop
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" bot.py
) else (
    python bot.py
)

echo [%date% %time%] Bot has stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
