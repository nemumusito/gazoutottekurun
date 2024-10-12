@echo off
chcp 65001 > nul
echo Starting the project...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Installing Python 3.10.6...
    
    REM Download Python 3.10.6 installer
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe', 'python-3.10.6-amd64.exe')"
    
    REM Install Python 3.10.6
    python-3.10.6-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
    
    REM Delete the installer
    del python-3.10.6-amd64.exe
    
    REM Update PATH
    setx PATH "%PATH%;C:\Program Files\Python310;C:\Program Files\Python310\Scripts" /M
    
    echo Python 3.10.6 has been installed.
    
    REM Restart the script to reflect the new environment variables
    echo Restarting the script to apply changes...
    start "" "%~f0"
    exit
) else (
    echo Python is already installed.
)

:CONTINUE_AFTER_PYTHON_INSTALL
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
