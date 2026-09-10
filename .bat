@echo off
if "%~1"=="RELAUNCHED" goto :main
start "Relic Tracker" cmd /k "%~f0" RELAUNCHED
exit /b

:main
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt -q
) else (
    call venv\Scripts\activate.bat
)

echo Starting Relic Tracker...
python src\main.py

pause