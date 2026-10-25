@echo off
title TikTok Automation Studio - Giai doan 1
cd /d "%~dp0\tiktok_pipeline_app"

echo =======================================================================
echo    DANG KHOI CHAY TIKTOK STUDIO - GIAI DOAN 1
echo =======================================================================
echo.
echo  Trinh duyet se tu dong mo tai dia chi:
echo  http://localhost:5150
echo.
echo  (Nhan Ctrl + C hoac dong cua so nay de tat ung dung)
echo =======================================================================
echo.

set "PYTHON_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" app.py
) else (
    python app.py 2>nul
    if %ERRORLEVEL% NEQ 0 (
        py app.py
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Khong the khoi chay Python hoac thieu thu vien.
    echo Neu day la may moi, hay chay file "Cai_Dat_May_Moi.bat" truoc!
    pause
)
