@echo off
REM Setup script for Plex Media Purge Helper Tool (Windows)

echo ============================================
echo Plex Media Purge Helper - Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Python found
python --version
echo.

REM Create virtual environment
echo [2/4] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping creation
) else (
    python -m venv venv
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Copy config template if config.py doesn't exist
echo [4/4] Setting up configuration...
if exist config.py (
    echo config.py already exists, skipping
) else (
    copy config.example.py config.py
    echo config.py created from template
    echo.
    echo IMPORTANT: Edit config.py and add your Plex and Tautulli credentials!
)
echo.

echo ============================================
echo Setup complete!
echo ============================================
echo.
echo Next steps:
echo 1. Edit config.py and add your API credentials
echo 2. Run: run.bat
echo.
echo Or manually:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run the tool: python main.py
echo.
pause
