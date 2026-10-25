@echo off
title Lay Code Moi Nhat Tu GitHub
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    DANG LAY MA NGUON MOI NHAT TU GITHUB VE MAY
echo =======================================================================
echo.
git pull origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo    [THANH CONG] May cua ban da dong bo 100%% code moi nhat!
    echo    Ban co the mo Web App de tiep tuc xay dung du an.
    echo =======================================================================
) else (
    echo.
    echo [CANH BAO] Khong the pull tu GitHub. Vui long kiem tra ket noi mang.
)
echo.
pause
