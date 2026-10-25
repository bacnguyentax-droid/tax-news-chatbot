@echo off
chcp 65001 >nul
title TikTok Studio - Ngrok HTTPS Tunnel (Port 5150)
cls

echo ===============================================================================
echo        TIKTOK AUTOMATION STUDIO 2026 - KHOI DONG DUONG HAM NGROK HTTPS
echo ===============================================================================
echo.
echo [*] Dang kiem tra cong cu ngrok tren may tinh cua ban...
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Chua tim thay lenh 'ngrok' trong bien moi truong PATH.
    echo.
    echo Ban co muon tu dong cai dat Ngrok bang cong cu Windows (winget)? (Y/N)
    set /p choice="Lua chon (Mac dinh Y): "
    if /i "%choice%"=="N" (
        echo.
        echo [Huong dan thu cong]
        echo 1. Truy cap: https://ngrok.com/download va tai ban zip cho Windows.
        echo 2. Giai nen file ngrok.exe vao thu muc du an hoac C:\Windows\System32.
        echo.
        pause
        exit /b
    )
    echo [*] Dang cai dat Ngrok qua winget...
    winget install Ngrok.Ngrok --accept-source-agreements --accept-package-agreements
    echo.
    echo [*] Tu dong cap nhat ngrok len ban moi nhat...
    ngrok update
    echo.
    echo [*] Neu moi cai dat xong, hay dong cua so CMD nay va chay lai de PATH nhan dien.
    echo.
    pause
    exit /b
)

echo [OK] Da tim thay cong cu Ngrok!
echo [*] Kiem tra phien ban hien tai...
ngrok --version
echo.
echo [*] Tu dong tat cac tien trinh ngrok cu dang chay ngam de tranh loi trung lap...
taskkill /F /IM ngrok.exe >nul 2>nul
timeout /t 1 /nobreak >nul
echo.
echo ===============================================================================
echo  LUU Y QUAN TRONG VE AUTHTOKEN:
echo  Neu day la lan dau chay Ngrok tren may tinh, ban can co AuthToken mien phi:
echo  1. Dang ky tai khoan mien phi tai: https://dashboard.ngrok.com/signup
echo  2. Lay token tai: https://dashboard.ngrok.com/get-started/your-authtoken
echo  3. Chay lenh: ngrok config add-authtoken ^<TOKEN_CUA_BAN^>
echo ===============================================================================
echo.
echo [*] Dang khoi dong duong ham HTTPS cho Localhost Port 5150...
echo [*] Sau khi man hinh Ngrok hien ra, ban hay copy duong dan HTTPS tai dong 'Forwarding'
echo     Vi du: https://xxxx-xx-xx.ngrok-free.app
echo [*] Sau do dan vao o 'Duong Ham HTTPS Cong Khai' trong giao dien Web app!
echo.
echo Nhan phim bat ky de bat dau Ngrok...
pause >nul

ngrok http 5150
