@echo off
chcp 65001 > nul
echo Starting the project...

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
start python image_scraper.py
if errorlevel 1 (
    echo Failed to start the scraping process. Please check your Python installation and try again.
    pause
    exit /b 1
)

REM Open Gradio interface in browser
timeout /t 5 /nobreak
start http://127.0.0.1:7860/

echo Gradio interface has been opened in your browser.
echo To exit the script, close this window.
pause
