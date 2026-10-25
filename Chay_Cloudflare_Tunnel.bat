@echo off
chcp 65001 >nul
title TikTok Studio - Cloudflare HTTPS Tunnel (Port 5150)
cls

python Chay_Cloudflare_Tunnel.py
if %ERRORLEVEL% NEQ 0 (
    pause
)
