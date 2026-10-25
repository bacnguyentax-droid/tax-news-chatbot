@echo off
title VPDT Automation - Cục Thuế TP.HCM
chcp 65001 >nul
cd /d "%~dp0"
echo Đang mở giao diện ứng dụng VPDT Automation...
start "" "C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe" run_vpdt_login.py
exit
