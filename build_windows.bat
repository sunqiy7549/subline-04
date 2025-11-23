@echo off
echo ==========================================
echo News Aggregator - Windows Build Script
echo ==========================================

echo [1/4] Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/4] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo [3/4] Installing Playwright browsers...
playwright install chromium

echo [4/4] Building executable...
pyinstaller news_aggregator.spec --clean --noconfirm

echo ==========================================
echo Build complete!
echo The executable is located in the 'dist' folder.
echo ==========================================
pause
