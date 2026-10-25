@echo off
title Cai Dat Moi Truong Cho May Moi - Manage App & TikTok Studio
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    DANG CAI DAT MOI TRUONG CHO MAY MOI (MANAGE APP ^& TIKTOK STUDIO)
echo =======================================================================
echo.
echo 1. Kiem tra Python tren may tinh...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] May tinh cua ban chua cai dat Python hoac chua them vao PATH!
    echo Vui long vao https://www.python.org/downloads/ de tai Python 3.10 tro len.
    echo *QUAN TRONG*: Nho tick chon vao o [Add Python to PATH] khi cai dat!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] Da tim thay: %%i

echo.
echo 2. Dang cap nhat pip va cai dat tat ca cac thu vien can thiet...
echo (Flask, Pandas, OpenPyXL, Pillow, Google Auth, Docx, PDF...)
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co the mot vai goi chua cai hoan tat, dang thu cai lai cac goi thiet yeu...
    python -m pip install flask flask-cors requests pandas openpyxl pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib python-docx mammoth pypdf reportlab beautifulsoup4 curl_cffi
)

echo.
echo =======================================================================
echo    DA HOAN TAT CAI DAT TAT CA THU VIEN THANH CONG!
echo.
echo    De khoi chay cac ung dung:
echo    - Chay TikTok Studio: Click file [Chay_TikTok_Studio.bat] (Cong 5150)
echo    - Chay Manage App   : Click file [Chay_Manage_App.bat]   (Cong 5100)
echo =======================================================================
echo.
pause
