@echo off
title CampusMail - Live Classroom Presentation Launcher
echo ======================================================================
echo           CampusMail Live Presentation & Classroom Sharing
echo ======================================================================
echo.
echo Starting Streamlit Local Server on Port 8501...
start "Streamlit Server" /min cmd /c ".\.venv\Scripts\streamlit.exe run app.py --server.headless true"

echo Starting Cloudflare Public HTTPS Tunnel for Classroom...
start "Cloudflare Tunnel" cmd /k ""C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8501"

echo.
echo ======================================================================
echo SUCCESS!
echo 1. Streamlit is running at: http://localhost:8501
echo 2. Check the Cloudflare Tunnel window for your public https://*.trycloudflare.com URL!
echo 3. The entire class can scan your QR code or open the link on their phones!
echo ======================================================================
pause
