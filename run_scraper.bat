@echo off
chcp 65001 > nul
echo Starting the project...

REM Check Python version
python --version
if errorlevel 1 (
    echo Failed to check Python version. Please make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Please check your Python installation.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment. Please check your installation.
    pause
    exit /b 1
)

REM Install requirements if requirements.txt exists
if exist requirements.txt (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install required packages. Please check your internet connection and try again.
        pause
        exit /b 1
    )
)

REM Run image_scraper.py
echo Starting the scraping process...
python image_scraper.py 2> error_log.txt
if errorlevel 1 (
    echo Failed to start the scraping process. Please check error_log.txt for more details.
    type error_log.txt
    pause
    exit /b 1
)

echo Script execution completed.
pause
