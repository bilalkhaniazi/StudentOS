@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Start StudentOS

set "DOCKER_DESKTOP=%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
if not exist "%DOCKER_DESKTOP%" set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"

docker info >nul 2>&1
if errorlevel 1 (
  echo Starting Docker Desktop...
  if exist "%DOCKER_DESKTOP%" (
    start "" "%DOCKER_DESKTOP%"
  ) else (
    echo Could not find Docker Desktop.
    echo Open it from the Start menu, wait until it is running, then double-click this file again.
    pause
    exit /b 1
  )
)

echo Waiting for Docker to be ready...
set /a tries=0
:wait_docker
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready
set /a tries+=1
if %tries% GEQ 80 (
  echo Docker did not become ready.
  echo Open Docker Desktop, wait for the whale icon, then double-click Start StudentOS again.
  pause
  exit /b 1
)
timeout /t 3 /nobreak >nul
goto wait_docker

:docker_ready
echo Starting StudentOS. You can close this window after the browser opens.
docker compose up -d
if errorlevel 1 (
  echo Could not start StudentOS. Make sure Docker Desktop is running, then try again.
  pause
  exit /b 1
)

start "" "http://127.0.0.1:43123"
echo StudentOS is running at http://127.0.0.1:43123
timeout /t 4 /nobreak >nul
exit /b 0
