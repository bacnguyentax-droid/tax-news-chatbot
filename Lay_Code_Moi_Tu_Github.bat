@echo off
title Lay Code Moi Nhat Tu GitHub
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    DANG LAY MA NGUON MOI NHAT TU GITHUB VE MAY
echo =======================================================================
echo.
echo Dang kiem tra va don dep xung dot du lieu bo nho tam (cache)...
git restore manage_app/chief_secretary_data.json 2>nul
git restore manage_app/admin_doc_reference_cache.json 2>nul
git restore tax_video_app/stage1_cache.json 2>nul

echo Dang tai ma nguon moi tu GitHub...
git pull origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo    [THANH CONG] May cua ban da dong bo 100%% code moi nhat!
    echo    Ban co the mo Web App de tiep tuc xay dung du an.
    echo =======================================================================
) else (
    echo.
    echo Dang thu che do dong bo uu tien ma nguon moi nhat tu GitHub...
    git stash
    git pull origin main
    git stash pop >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo =======================================================================
        echo    [THANH CONG] May cua ban da dong bo 100%% code moi nhat!
        echo =======================================================================
    ) else (
        echo.
        echo [CANH BAO] Khong the pull tu GitHub. Vui long kiem tra ket noi mang hoac xung dot code.
    )
)
echo.
pause
