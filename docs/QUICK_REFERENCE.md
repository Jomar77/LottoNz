# LottoNZ Scheduled Scraper - Quick Reference

## Installation
```bash
cd Backend
pip install -r requirements.txt
```

## Setup Tasks
```bash
# Run as Administrator
setup_scheduler.bat      # Creates weekly Sunday 5 PM task
run_on_startup.bat       # Creates startup catch-up task
```

## Testing
```bash
# Test scraper directly
python dataScrape\mylotto_scraper.py

# Test scheduler logic
python dataScrape\scheduler.py
```

## Monitoring
```bash
# View logs
type dataScrape\scraper.log

# View last run status
type dataScrape\last_run.json

# View scraped data
type lotto-data\lotto_results.csv
```

## Task Management
```bash
# List tasks
schtasks /query /tn LottoNZ_Weekly_Scraper
schtasks /query /tn LottoNZ_Startup_Check

# Run manually
schtasks /run /tn LottoNZ_Weekly_Scraper

# Delete tasks
schtasks /delete /tn LottoNZ_Weekly_Scraper /f
schtasks /delete /tn LottoNZ_Startup_Check /f
```

## Force Run
```bash
# Delete tracking file and run
del dataScrape\last_run.json
python dataScrape\scheduler.py
```

## Files Created
- `Backend/requirements.txt` - Python dependencies
- `Backend/.env` - Environment configuration
- `Backend/.env.example` - Configuration template
- `Backend/dataScrape/mylotto_scraper.py` - Main scraper
- `Backend/dataScrape/scheduler.py` - Scheduling logic
- `Backend/dataScrape/last_run.json` - Run tracker (auto-generated)
- `Backend/dataScrape/scraper.log` - Log file (auto-generated)
- `Backend/setup_scheduler.bat` - Weekly task setup
- `Backend/run_on_startup.bat` - Startup task setup
- `Backend/README.md` - Detailed documentation
- `SETUP_GUIDE.md` - Complete setup instructions

## Schedule Details
- **Weekly Task**: Every Sunday at 5:00 PM
- **Startup Task**: 2 minutes after PC starts (only if >7 days since last run)
- **Duplicate Prevention**: Checks `last_run.json` before running
- **Log Rotation**: Max 10MB per file, keeps 5 backups

## Troubleshooting
1. **Import errors**: Run `pip install -r requirements.txt`
2. **WebDriver errors**: Update Firefox and geckodriver
3. **No data found**: Inspect mylotto.co.nz HTML structure and update parsing logic
4. **Task not running**: Check Task Scheduler history and logs

## Configuration (.env)
```ini
# Optional: Only set if Firefox in non-standard location
# FIREFOX_PATH=C:\Custom\Path\To\firefox.exe

MYLOTTO_URL=https://mylotto.co.nz/game-information
MAX_RETRIES=3
RETRY_DELAY=60
LOG_LEVEL=INFO
```

Note: Geckodriver is automatically downloaded and managed.

## Full Documentation
See `SETUP_GUIDE.md` for complete instructions and troubleshooting.
