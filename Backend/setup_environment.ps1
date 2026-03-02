# LottoNZ Backend - Environment Setup Script
# Fixes virtual environment and installs all dependencies
# For Windows PowerShell

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "LottoNZ Backend Environment Setup" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in Backend directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "ERROR: This script must be run from the Backend directory" -ForegroundColor Red
    Write-Host "Please run: cd Backend" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host $pythonVersion -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ or add it to your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Delete existing .venv if it exists (clean start)
if (Test-Path ".venv") {
    Write-Host "Step 2: Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
    Write-Host "Old .venv removed" -ForegroundColor Green
} else {
    Write-Host "Step 2: No existing .venv found (clean install)" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 3: Creating fresh virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Virtual environment created: Backend\.venv" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

Write-Host "Step 6: Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install requirements" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

Write-Host "Step 7: Installing dev dependencies..." -ForegroundColor Yellow
pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Failed to install dev dependencies (non-critical)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 8: Verifying installation..." -ForegroundColor Yellow
python -c "import selenium; print(f'✓ Selenium {selenium.__version__}')"
python -c "import pandas; print(f'✓ Pandas {pandas.__version__}')"
python -c "import pytest; print(f'✓ Pytest {pytest.__version__}')"
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Virtual environment: Backend\.venv" -ForegroundColor White
Write-Host ""
Write-Host "To activate in future sessions:" -ForegroundColor White
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "To test the scraper:" -ForegroundColor White
Write-Host "  python scripts\run_scheduler.py --now" -ForegroundColor Gray
Write-Host ""
Write-Host "To run tests:" -ForegroundColor White
Write-Host "  pytest tests\" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
