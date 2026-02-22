# LottoNZ Scheduled Scraper - Setup Guide

## Quick Start

Follow these steps to set up the automated weekly lottery scraper:

### Step 1: Install Dependencies

Open Command Prompt or PowerShell in the Backend directory and run:

```bash
cd C:\Users\jomna\Documents\GitHub\LottoNz\Backend
pip install -r requirements.txt
```

This installs:
- selenium (web automation)
- beautifulsoup4 (HTML parsing)
- requests (HTTP requests)
- pandas (data processing)
- openpyxl (Excel file handling)
- python-dotenv (environment configuration)
- webdriver-manager (automatic geckodriver management)

### Step 2: Verify Firefox is Installed

The scraper uses Firefox and will automatically download geckodriver on first run.

Check if Firefox is installed:
```bash
"C:\Program Files\Mozilla Firefox\firefox.exe" --version
```

If Firefox is not installed or in a different location, either:
- Install Firefox from: https://www.mozilla.org/firefox/
- Or set `FIREFOX_PATH` in `.env` file with your Firefox location

### Step 3: Test the Scraper Manually

Before scheduling, test that everything works:

```bash
cd dataScrape
python mylotto_scraper.py
```

On first run, you'll see geckodriver being downloaded automatically:
```
INFO - Setting up geckodriver (will auto-download if needed)...
[WDM] - Downloading: 100%|████████████████| 2.11M/2.11M [00:01<00:00, 1.23MB/s]
INFO - WebDriver initialized successfully
```

Expected output:
```
INFO - WebDriver initialized successfully
INFO - Fetching URL: https://mylotto.co.nz/game-information (attempt 1/3)
INFO - Page loaded successfully
INFO - Found X document elements
INFO - Parsed Y lottery entries
INFO - Wrote Y rows to ...\lotto-data\lotto_results.csv
INFO - === Scraping completed successfully. Y rows written ===
```

### Step 4: Test the Scheduler

Test the scheduling logic:

```bash
python scheduler.py
```

Expected output (first run):
```
INFO - No previous successful run found. Should run scraper.
INFO - Executing scraper...
[... scraper output ...]
INFO - === Scraper completed successfully ===
```

If you run it again immediately:
```
INFO - Last successful run: 2026-02-22T17:00:00 (0 days ago)
INFO - Scraper already ran recently. Skipping.
```

### Step 5: Set Up Scheduled Tasks

#### 5a. Weekly Sunday 5 PM Task

Right-click `setup_scheduler.bat` and select "Run as administrator" (or just double-click if you have permissions).

This creates a Windows Task Scheduler task that runs every Sunday at 5:00 PM.

#### 5b. Startup Catch-up Task

Right-click `run_on_startup.bat` and select "Run as administrator".

This creates a task that runs 2 minutes after PC startup to catch any missed scrapes.

### Step 6: Verify Tasks Are Created

Open Task Scheduler:
1. Press `Win + R`
2. Type `taskschd.msc` and press Enter
3. Look for:
   - **LottoNZ_Weekly_Scraper** (runs Sundays at 5 PM)
   - **LottoNZ_Startup_Check** (runs at startup)

Or check via command line:
```bash
schtasks /query /tn LottoNZ_Weekly_Scraper
schtasks /query /tn LottoNZ_Startup_Check
```

## Usage

### Monitor Scraper Activity

**View logs:**
```bash
type dataScrape\scraper.log
```

**View last run status:**
```bash
type dataScrape\last_run.json
```

**View scraped data:**
```bash
type lotto-data\lotto_results.csv
```

### Manual Operations

**Run scraper manually:**
```bash
schtasks /run /tn LottoNZ_Weekly_Scraper
```

Or directly:
```bash
python dataScrape\scheduler.py
```

**Force scraper (bypass date check):**
```bash
# Delete last_run.json to force a run
del dataScrape\last_run.json
python dataScrape\scheduler.py
```

### Troubleshooting

**Problem: Scraper not finding elements**

The HTML structure of mylotto.co.nz may have changed. You'll need to inspect the page and update the parsing logic in `mylotto_scraper.py`:

1. Open https://mylotto.co.nz/game-information in Firefox
2. Right-click the lottery data and select "Inspect Element"
3. Find the actual class names and structure
4. Update the `parse_lottery_data()` method in `mylotto_scraper.py`

**Problem: WebDriver errors**

- Ensure Firefox is installed
- On first run, geckodriver downloads automatically (requires internet)
- Update Firefox to latest version: https://www.mozilla.org/firefox/
- If Firefox is in a non-standard location, set `FIREFOX_PATH` in `.env`

**Problem: Task not running**

1. Check Task Scheduler history:
   - Open Task Scheduler
   - Click on the task
   - View "History" tab
2. Check logs: `type dataScrape\scraper.log`
3. Verify Python is in your system PATH

**Problem: CSV format doesn't match**

The scraper currently writes only 6 numbers per row (matching existing format). If you need dates/powerball:
1. Uncomment the date extraction in `save_to_csv()` method
2. Adjust CSV writer to include additional columns

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Windows Task Scheduler                       │
├─────────────────────────────────────────────────────┤
│  • Weekly Trigger: Sunday 5 PM                       │
│  • Startup Trigger: At boot + 2min delay             │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  scheduler.py  │
         └───────┬────────┘
                 │
        ┌────────┴─────────┐
        │                  │
        ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ last_run.json│   │ scraper.log  │
│  (tracker)   │   │  (rotating)  │
└──────────────┘   └──────────────┘
        │
        ▼ (if should run)
┌──────────────────────┐
│ mylotto_scraper.py   │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────────┐  ┌────────────────┐
│ mylotto.co │  │ lotto_results  │
│   .nz      │  │    .csv        │
│ (scrape)   │  │  (append)      │
└────────────┘  └────────────────┘
```

## Configuration Options

Edit `.env` to customize:

```ini (optional - only if Firefox in non-standard location)
# FIREFOX_PATH=C:\Path\To\Firefox\firefox.exe
GECKODRIVER_PATH=C:\Users\jomna\Downloads\geckodriver.exe

# Target URL
MYLOTTO_URL=https://mylotto.co.nz/game-information

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Retry behavior
MAX_RETRIES=3       # Number of retry attempts
RETRY_DELAY=60      # Seconds between retries
```

## Next Steps

Once the scraper is running successfully:

1. **Integrate with frontend pipeline:**
   - Ensure CSV format matches expectations
   - Update `convert_to_json.py` if needed
   - Verify `Frontend/public/results.json` updates correctly

2. **Monitor for a few weeks:**
   - Check logs weekly
   - Verify data quality
   - Adjust retry settings if needed

3. **Optional enhancements:**
   - Add email notifications on failure
   - Create dashboard for monitoring
   - Automate the CSV → Excel → JSON pipeline

## Support

- Check logs: `dataScrape\scraper.log`
- View last run: `dataScrape\last_run.json`
- Test manually: `python dataScrape\mylotto_scraper.py`
- View Backend README: `Backend\README.md`

## Important Notes

⚠️ **HTML Structure Dependency**: The scraper relies on the CSS class `lnz-document-group__document`. If mylotto.co.nz changes their HTML, the scraper will need to be updated.

⚠️ **PC Must Be On**: For the scheduled task to run, your PC must be on and awake at the scheduled time. The startup task will catch missed runs if the PC was off.

⚠️ **Network Required**: The scraper requires internet connectivity to access mylotto.co.nz.

✅ **Duplicate Prevention**: The scheduler automatically prevents running multiple times in the same week via `last_run.json`.

✅ **Log Rotation**: Logs automatically rotate at 10MB to prevent disk space issues.
