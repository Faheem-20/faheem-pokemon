@echo off
setlocal
cd /d "%~dp0"
title Pokemon Nexus Django Backend

echo ==============================================
echo  Pokemon Nexus - JWT + Role Based Backend
echo ==============================================
echo.

if not exist "backend\manage.py" (
  echo ERROR: backend\manage.py not found.
  echo Please extract the ZIP first, then run this file from Pokemon_Nexus_Complete_Project folder.
  pause
  exit /b 1
)

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

if not exist "backend\venv\Scripts\python.exe" (
  echo Creating virtual environment inside backend folder...
  %PYTHON_CMD% -m venv "backend\venv"
  if errorlevel 1 (
    echo ERROR: Could not create venv.
    pause
    exit /b 1
  )
)

call "backend\venv\Scripts\activate.bat"
python -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
  echo ERROR: requirements install failed.
  pause
  exit /b 1
)

cd /d "%~dp0backend"
python manage.py makemigrations users
python manage.py migrate
if errorlevel 1 (
  echo ERROR: database migration failed.
  pause
  exit /b 1
)

echo.
echo Backend ready. Keep this window open.
echo Register API: http://127.0.0.1:5000/api/auth/register
echo Login API:    http://127.0.0.1:5000/api/auth/login
echo Profile API:  http://127.0.0.1:5000/api/auth/profile
echo Admin API:    http://127.0.0.1:5000/api/auth/admin/stats
echo.
python manage.py runserver 127.0.0.1:5000
pause
