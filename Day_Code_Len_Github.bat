@echo off
title Day Code Len GitHub
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    DANG DONG BO TOAN BO CODE MOI LEN GITHUB
echo =======================================================================
echo.
git add .
git commit -m "Dong bo ma nguon ngay %date% luc %time%"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo    [THANH CONG] Toan bo ma nguon da duoc day len GitHub!
    echo    Tren may con lai, ban chi can chay: [Lay_Code_Moi_Tu_Github.bat]
    echo =======================================================================
) else (
    echo.
    echo [THONG BAO] Khong co thay doi moi de push hoac gap su co ket noi.
)
echo.
pause
