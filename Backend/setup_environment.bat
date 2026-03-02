@echo off
REM ============================================================================
REM LottoNZ Backend - Environment Setup Script
REM Fixes virtual environment and installs all dependencies
REM ============================================================================

echo ========================================================================
echo LottoNZ Backend Environment Setup
echo ========================================================================
echo.

REM Check if we're in Backend directory
if not exist "requirements.txt" (
    echo ERROR: This script must be run from the Backend directory
    echo Please run: cd Backend
    pause
    exit /b 1
)

echo Step 1: Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found in PATH
    echo Please install Python 3.8+ or add it to your PATH
    pause
    exit /b 1
)

python --version
echo.

REM Delete existing .venv if it exists (clean start)
if exist ".venv" (
    echo Step 2: Removing old virtual environment...
    rmdir /s /q .venv
    echo Old .venv removed
) else (
    echo Step 2: No existing .venv found (clean install)
)
echo.

echo Step 3: Creating fresh virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created: Backend\.venv
echo.

echo Step 4: Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

echo Step 5: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 6: Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo.

echo Step 7: Installing dev dependencies...
pip install -r requirements-dev.txt
if errorlevel 1 (
    echo WARNING: Failed to install dev dependencies (non-critical)
)
echo.

echo Step 8: Verifying installation...
python -c "import selenium; print(f'✓ Selenium {selenium.__version__}')"
python -c "import pandas; print(f'✓ Pandas {pandas.__version__}')"
python -c "import pytest; print(f'✓ Pytest {pytest.__version__}')"
echo.

echo ========================================================================
echo ✓ Setup Complete!
echo ========================================================================
echo.
echo Virtual environment: Backend\.venv
echo.
echo To activate in future sessions:
echo   .venv\Scripts\activate
echo.
echo To test the scraper:
echo   python scripts\run_scheduler.py --now
echo.
echo To run tests:
echo   pytest tests\
echo.
echo ========================================================================
pause
