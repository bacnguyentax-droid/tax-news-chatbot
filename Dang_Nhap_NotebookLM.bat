@echo off
title Dang Nhap Google NotebookLM - Tu Dong Nap Nguon
cd /d "%~dp0"
chcp 65001 >nul

echo =======================================================================
echo    DANG NHAP GOOGLE NOTEBOOKLM (XAC THUC PHIEN LAM VIEC 100%% TU DONG)
echo =======================================================================
echo.
echo  Cua so trinh duyet Microsoft Edge se duoc mo tren man hinh...
echo  Vui long dang nhap tai khoan: bacnguyentax@gmail.com
echo.
echo  * LUU Y QUAN TRONG:
echo  1. Nhap email va mat khau Google cua ban vao cua so Edge.
echo  2. Cho trinh duyet load vao toi man hinh chinh cua NotebookLM (noi co nut 'New notebook').
echo  3. Sau khi vao toi man hinh chinh, he thong se tu dong ghi nhan va dong cua so!
echo.
echo =======================================================================
echo.

set "PYTHON_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m notebooklm login --fresh --browser msedge
) else (
    python -m notebooklm login --fresh --browser msedge
)

echo.
echo =======================================================================
echo    DA HOAN TAT TIEN TRINH XAC THUC NOTEBOOKLM!
echo    Vui long tai lai trang Web App (F5) de thay trang thai Xanh la cay!
echo =======================================================================
pause
