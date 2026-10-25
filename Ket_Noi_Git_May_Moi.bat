@echo off
title Ket Noi Kho Git Cho May Moi
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    KET NOI DU AN TREN LAPTOP VOI KHO LUU TRU GITHUB
echo =======================================================================
echo.
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] May tinh cua ban chua cai dat Git!
    echo Vui long vao https://git-scm.com/downloads de tai va cai dat Git.
    echo.
    pause
    exit /b 1
)

if not exist .git (
    echo Dang khoi tao Git va ket noi voi GitHub...
    git init
    git remote add origin https://github.com/bacnguyentax-droid/tax-news-chatbot.git
    git branch -M main
    git fetch origin main
    git reset --mixed origin/main
    echo [OK] Da ket noi thanh cong voi GitHub!
) else (
    echo [OK] Thu muc nay da duoc ket noi san voi Git.
)

echo.
echo =======================================================================
echo    HOAN TAT!
echo    - De lay code moi tu may ban ve laptop : Chay [Lay_Code_Moi_Tu_Github.bat]
echo    - De day code tu laptop ve may ban     : Chay [Day_Code_Len_Github.bat]
echo =======================================================================
echo.
pause
