@echo off
echo Starting AI Stock Agent Daily Update...
cd /d "%~dp0"
python scripts/update_daily.py
echo.
echo Update Complete!
pause
