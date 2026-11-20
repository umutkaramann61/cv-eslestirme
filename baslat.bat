@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Gerekli paketler kuruluyor (ilk seferde biraz surer)...
python -m pip install -q flask pypdf python-docx anthropic
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=deneme123
echo.
echo Yonetici sifresi (yerel deneme): %ADMIN_PASSWORD%
echo Yapay zeka icin once:  set ANTHROPIC_API_KEY=sk-ant-...
start "" http://127.0.0.1:5000
python app.py
pause
