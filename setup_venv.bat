@echo off
REM Setup script for creating Python 3.12 virtual environment on Windows

echo ========================================
echo SmartSpendGrocery - Virtual Environment Setup
echo ========================================
echo.

REM Check if Python 3.12 is available
python3.13 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Checking for Python 3.13 using py launcher...
    py -3.13 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python 3.13 not found!
        echo.
        echo Please install Python 3.13 from https://www.python.org/downloads/
        echo Or use: winget install Python.Python.3.13
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py -3.13
    )
) else (
    set PYTHON_CMD=python3.13
)

echo Python 3.13 found!
echo.

REM Remove old virtual environment if it exists
if exist adkapp (
    echo Removing old virtual environment...
    rmdir /s /q adkapp
    echo Old virtual environment removed.
    echo.
)

REM Create new virtual environment
echo Creating new virtual environment with Python 3.13...
%PYTHON_CMD% -m venv adkapp
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

REM Activate and upgrade pip
echo Activating virtual environment and upgrading pip...
call adkapp\Scripts\activate.bat
python -m pip install --upgrade pip
echo.

REM Install requirements
echo Installing project dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo WARNING: Some packages may have failed to install.
    echo Please check the output above.
    echo.
) else (
    echo.
    echo ========================================
    echo Setup completed successfully!
    echo ========================================
    echo.
    echo To activate the virtual environment in the future, run:
    echo   adkapp\Scripts\activate
    echo.
    echo To run the application:
    echo   streamlit run main.py
    echo.
)

pause

