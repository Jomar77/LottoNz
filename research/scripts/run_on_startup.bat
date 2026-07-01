@echo off
REM ============================================================================
REM LottoNZ Startup Check - Task Scheduler Setup
REM Creates a task to check for missed scrapes when PC starts up
REM ============================================================================

echo Setting up LottoNZ Startup Check Task...
echo.

REM Configuration
set TASK_NAME=LottoNZ_Startup_Check
set PYTHON_PATH=python
set SCRIPT_PATH=%~dp0dataScrape\scheduler.py

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

REM Create the startup task with delay
echo Creating startup task...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc onstart ^
    /delay 0002:00 ^
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
echo Trigger: At system startup (2 minute delay)
echo Purpose: Checks for missed weekly scrapes and runs if needed
echo Script: %SCRIPT_PATH%
echo.
echo To view the task:    schtasks /query /tn "%TASK_NAME%" /v /fo LIST
echo To run manually:     schtasks /run /tn "%TASK_NAME%"
echo To delete task:      schtasks /delete /tn "%TASK_NAME%" /f
echo ============================================================================
echo.

pause
