@echo off
REM Run script for Plex Media Purge Helper Tool (Windows)

REM Check if virtual environment exists
if not exist venv (
    echo Error: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment and run the tool
call venv\Scripts\activate.bat
python main.py %*
