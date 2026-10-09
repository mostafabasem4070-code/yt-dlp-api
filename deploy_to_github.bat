@echo off
chcp 65001 >nul
title GitHub Deployer - YouTube API Hub
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_to_github.ps1" %*
echo.
pause
