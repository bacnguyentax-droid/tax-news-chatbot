@echo off
title Dang Nhap Google NotebookLM - Tu Dong Nap Nguon
cd /d "%~dp0"

echo =======================================================================
echo    DANG NHAP GOOGLE NOTEBOOKLM (XAC THUC PHIEN LAM VIEC 100%% TU DONG)
echo =======================================================================
echo.
echo  Cua so trinh duyet Microsoft Edge se duoc mo tren man hinh...
echo  Quy khach vui long dang nhap hoac chon tai khoan Google cua minh.
echo  Sau khi dang nhap thanh cong, cua so se tu dong luu va dong lai!
echo.
echo =======================================================================
echo.

set "PYTHON_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m notebooklm login --browser msedge
) else (
    python -m notebooklm login --browser msedge
)

echo.
echo =======================================================================
echo    DA HOAN TAT TIEN TRINH XAC THUC NOTEBOOKLM!
echo =======================================================================
pause
