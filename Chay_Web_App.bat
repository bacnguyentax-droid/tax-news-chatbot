@echo off
title Tax Video AI Bot - Web Edition
chcp 65001 >nul
cd /d "%~dp0tax_video_app"

echo =======================================================================
echo    DANG KHOI CHAY TAX VIDEO AI BOT - PHIEN BAN WEB EDITION
echo =======================================================================
echo.
echo  Trinh duyet se tu dong mo tai dia chi:
echo  http://localhost:5050
echo.
echo  (Nhan Ctrl + C hoac dong cua so nay de tat ung dung)
echo =======================================================================
echo.

start "" "http://localhost:5050"

set "PYTHON_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" web_app.py
) else (
    python web_app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [THONG BAO] Neu web app da duoc mo san tren cong 5050, hay truy cap:
    echo http://localhost:5050
    pause
)
