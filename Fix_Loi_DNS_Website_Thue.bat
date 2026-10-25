@echo off
chcp 65001 >nul
echo ========================================================
echo    CÔNG CỤ KHẮC PHỤC LỖI DNS CÁC TRANG WEB THUẾ & BỘ TÀI CHÍNH
echo    (Sửa lỗi DNS_PROBE_FINISHED_NXDOMAIN trên mạng Viettel / VNPT / FPT)
echo ========================================================
echo.

:: Kiểm tra quyền Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [CẢNH BÁO] Bạn cần bấm CHUỘT PHẢI vào file này và chọn:
    echo            "RUN AS ADMINISTRATOR" (Chạy với quyền Quản trị viên).
    echo.
    pause
    exit /b
)

set HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts

echo Đang bổ sung địa chỉ IP máy chủ chính phủ vào tệp hosts...
echo. >> "%HOSTS_FILE%"
echo # Cau hinh fix loi DNS cac trang web Chinh phu (Tao boi Manage App) >> "%HOSTS_FILE%"
echo 103.9.200.37 gdt.gov.vn >> "%HOSTS_FILE%"
echo 182.236.113.55 mof.gov.vn >> "%HOSTS_FILE%"
echo 182.236.113.55 www.mof.gov.vn >> "%HOSTS_FILE%"
echo 140.150.43.6 vbpl.vn >> "%HOSTS_FILE%"

echo.
echo Đang xóa bộ nhớ đệm DNS (Flush DNS)...
ipconfig /flushdns >nul

echo.
echo ========================================================
echo [THÀNH CÔNG] ĐÃ KHẮC PHỤC XONG LỖI DNS!
echo Giờ bạn có thể mở gdt.gov.vn và mof.gov.vn bình thường trên Google Chrome.
echo ========================================================
echo.
pause
