@echo off
setlocal EnableExtensions
title Cursor worker (for chat)
cd /d "%~dp0"
echo This window is the Cursor worker for chat edits.
echo Leave it open. It is not required to run StudentOS.
echo.
powershell -ExecutionPolicy Bypass -NoExit -Command "agent worker start --worker-dir 'C:\Users\Bilal Khan\Documents\Masters Project' --name 'Bilal PC'"
