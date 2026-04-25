@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=%SCRIPT_DIR%.venv"
set "REQUIREMENTS_FILE=%SCRIPT_DIR%requirements.txt"
set "STAMP_FILE=%VENV_DIR%\.requirements-installed"

if "%PYTHON_BIN%"=="" (
  set "PYTHON_BIN=python"
)

echo ========================================
echo automysqlback local dev startup (Windows)
echo directory: %SCRIPT_DIR%
echo ========================================

where "%PYTHON_BIN%" >nul 2>nul
if errorlevel 1 (
  echo ERROR: cannot find %PYTHON_BIN%. Please install Python 3 and add it to PATH.
  exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo First run detected, creating virtual environment...
  "%PYTHON_BIN%" -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo ERROR: failed to create virtual environment.
    exit /b 1
  )
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo ERROR: virtual environment Python not found: %VENV_PYTHON%
  exit /b 1
)

set "NEEDS_INSTALL=0"
if not exist "%STAMP_FILE%" set "NEEDS_INSTALL=1"

if not exist "%REQUIREMENTS_FILE%" (
  echo ERROR: requirements.txt not found.
  exit /b 1
)
if exist "%STAMP_FILE%" (
  powershell -NoProfile -Command "exit [int]((Get-Item '%REQUIREMENTS_FILE%').LastWriteTime -gt (Get-Item '%STAMP_FILE%').LastWriteTime)"
  if errorlevel 1 set "NEEDS_INSTALL=1"
)

"%VENV_PYTHON%" -c "import flask" >nul 2>nul
if errorlevel 1 set "NEEDS_INSTALL=1"

if "%NEEDS_INSTALL%"=="1" (
  echo Installing or updating backend dependencies...
  "%VENV_PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  "%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS_FILE%"
  if errorlevel 1 exit /b 1
  type nul > "%STAMP_FILE%"
) else (
  echo Dependencies are ready. Skip installation.
)

echo Starting backend service...
echo URL: http://127.0.0.1:7001
echo Press Ctrl+C to stop the service.
echo.

"%VENV_PYTHON%" "%SCRIPT_DIR%start.py"
exit /b %errorlevel%
