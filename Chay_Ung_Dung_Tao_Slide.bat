@echo off
chcp 65001 >nul
title TRÌNH TẠO SLIDE & INFOGRAPHIC CHUYÊN NGHIỆP

echo ================================================================
echo    🚀 ĐANG KHỞI CHẠY TRÌNH TẠO ẢNH SLIDE & INFOGRAPHIC
echo ================================================================
echo.
echo  Giao diện web sẽ tự động mở trên trình duyệt mặc định của bạn...
echo  Địa chỉ: http://localhost:8520
echo.
echo  Để dừng ứng dụng, bạn chỉ cần đóng cửa sổ màu đen này lại.
echo ================================================================
echo.

cd /d "%~dp0\slide_creator_app"
python server.py

pause
