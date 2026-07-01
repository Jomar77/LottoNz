@echo off
REM ============================================================================
REM LottoNZ Weekly Scraper - Task Scheduler Setup
REM Creates a scheduled task to run the scraper every Sunday at 5:00 PM
REM ============================================================================

echo Setting up LottoNZ Weekly Scraper Task Scheduler...
echo.

REM Configuration
set TASK_NAME=LottoNZ_Weekly_Scraper
set PYTHON_PATH=python
set SCRIPT_PATH=%~dp0dataScrape\scheduler.py
set LOG_PATH=%~dp0dataScrape\scraper.log

REM Check if Python is available
%PYTHON_PATH% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

echo Python found: 
%PYTHON_PATH% --version
echo.

REM Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo ERROR: scheduler.py not found at %SCRIPT_PATH%
    pause
    exit /b 1
)

echo Script path: %SCRIPT_PATH%
echo.

REM Delete existing task if it exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo Existing task found. Deleting...
    schtasks /delete /tn "%TASK_NAME%" /f
)

REM Create the scheduled task
echo Creating new scheduled task...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc weekly ^
    /d SUN ^
    /st 17:00 ^
    /rl HIGHEST ^
    /f

if errorlevel 1 (
    echo ERROR: Failed to create scheduled task
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Task created successfully!
echo ============================================================================
echo Task Name: %TASK_NAME%
echo Schedule: Every Sunday at 5:00 PM
echo Script: %SCRIPT_PATH%
echo Log File: %LOG_PATH%
echo.
echo To view the task:    schtasks /query /tn "%TASK_NAME%" /v /fo LIST
echo To run manually:     schtasks /run /tn "%TASK_NAME%"
echo To delete task:      schtasks /delete /tn "%TASK_NAME%" /f
echo ============================================================================
echo.

REM Export task XML for version control
set XML_PATH=%~dp0task_schedule.xml
schtasks /query /tn "%TASK_NAME%" /xml > "%XML_PATH%"
echo Task definition exported to: %XML_PATH%
echo.

pause
