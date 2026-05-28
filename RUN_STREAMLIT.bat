@echo off
REM Quick Start Script for F1 Streamlit Dashboard

echo ========================================
echo  F1 Predictions ^& Analytics Dashboard
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    py -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Launch Streamlit app
echo.
echo ========================================
echo  Launching Streamlit Dashboard...
echo  Opening browser automatically
echo ========================================
echo.
streamlit run streamlit_app.py

pause
