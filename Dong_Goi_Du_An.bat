@echo off
title Dong Goi Du An Sang May Khac
cd /d "%~dp0"
chcp 65001 >nul
echo =======================================================================
echo    DANG DONG GOI DU AN DE CHUYEN SANG LAPTOP / MAY KHAC
echo =======================================================================
echo.
echo He thong dang tu dong loc bo cac thu muc rac/nang:
echo (node_modules, .next, build, dist, scratch, __pycache__...)
echo giup tao file ZIP nho gon, nhe nhat, giu nguyen 100%% code, data va token.
echo.
echo Vui long cho trong giay lat...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$src = '%~dp0'.TrimEnd('\'); $dest = Join-Path (Split-Path $src -Parent) 'Chat_bot_Gemini_Goi_Di.zip'; if (Test-Path $dest) { Remove-Item $dest -Force }; $items = Get-ChildItem -Path $src | Where-Object { $_.Name -notin @('node_modules', '.next', 'build', 'dist', 'chrome_temp', 'scratch', '__pycache__', 'deno.exe') -and $_.Extension -ne '.zip' }; Compress-Archive -Path $items.FullName -DestinationPath $dest -CompressionLevel Optimal; Write-Host ''; Write-Host '>>> DA TAO FILE NEN THANH CONG: ' -NoNewline; Write-Host $dest -ForegroundColor Green; Write-Host ('>>> Dung luong file: ' + [math]::Round((Get-Item $dest).Length / 1MB, 2) + ' MB' ) -ForegroundColor Cyan; explorer.exe /select,$dest"

echo.
echo =======================================================================
echo    HOAN TAT! Thu muc chua file "Chat_bot_Gemini_Goi_Di.zip" da duoc mo.
echo.
echo    CAC BUOC TIEP THEO TREN LAPTOP:
echo    1. Chep file "Chat_bot_Gemini_Goi_Di.zip" sang Laptop (USB / Drive / Zalo).
echo    2. Giai nen (Extract All) thanh mot thu muc tren Laptop.
echo    3. Click dup vao [Cai_Dat_May_Moi.bat] de tu dong cai dat thu vien.
echo    4. Click [Chay_TikTok_Studio.bat] hoac [Chay_Manage_App.bat] de su dung!
echo =======================================================================
echo.
pause
