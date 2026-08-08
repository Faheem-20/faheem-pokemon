@echo off
setlocal
cd /d "%~dp0"
title Pokemon Nexus Local Frontend Server

echo ==============================================
echo  Pokemon Nexus - Local Frontend Server (Port 8000)
echo ==============================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PYTHON_CMD=py -3"
if "%PYTHON_CMD%"=="" (
  where python >nul 2>nul
  if %errorlevel%==0 set "PYTHON_CMD=python"
)
if "%PYTHON_CMD%"=="" (
  echo ERROR: Python is not installed or not added to PATH.
  echo Install Python and tick Add Python to PATH, then try again.
  pause
  exit /b 1
)

echo Starting local frontend server on http://localhost:8000/ ...
echo Keep this window open while playing!
echo.

start "" "http://localhost:8000/"
%PYTHON_CMD% -m http.server 8000
pause
