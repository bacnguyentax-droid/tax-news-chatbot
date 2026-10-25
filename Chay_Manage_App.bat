@echo off
title Manage App - He Thong Quet & Tai Van Ban Google Drive
cd /d "%~dp0\manage_app"

echo =======================================================================
echo    DANG KHOI CHAY MANAGE APP - QUET & TAI VAN BAN GOOGLE DRIVE
echo =======================================================================
echo.
echo  Trinh duyet se tu dong mo tai dia chi:
echo  http://localhost:5055
echo.
echo  (Nhan Ctrl + C hoac dong cua so nay de tat ung dung)
echo =======================================================================
echo.

start "" http://localhost:5055

set "PYTHON_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" app.py
) else (
    python app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung gap su co hoac bi dong dot ngot.
    pause
)
