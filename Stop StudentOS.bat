@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Stop StudentOS

docker compose down
if errorlevel 1 (
  echo Could not stop StudentOS. Open Docker Desktop, wait until it is running, then try again.
  pause
  exit /b 1
)

echo StudentOS has been stopped.
timeout /t 3 /nobreak >nul
exit /b 0
