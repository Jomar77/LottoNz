# LottoNZ Backend

Backend services for the LottoNZ lottery analysis application.

## Setup

### Prerequisites

- Python 3.8 or higher
- Firefox browser (geckodriver will be automatically downloaded)

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create environment configuration (optional):
```bash
copy .env.example .env
```

3. Edit `.env` file only if needed:
- Set `FIREFOX_PATH` only if Firefox is in a non-standard location
- Geckodriver is automatically downloaded and managed by webdriver-manager

### Setting Up the Scheduled Scraper

The scheduled scraper runs every Sunday at 5:00 PM to fetch the latest lottery data from mylotto.co.nz.

#### Automatic Setup (Recommended)

1. Run the scheduler setup script:
```bash
setup_scheduler.bat
```

2. Run the startup check setup script:
```bash
run_on_startup.bat
```

This creates two Windows scheduled tasks:
- **LottoNZ_Weekly_Scraper**: Runs every Sunday at 5:00 PM
- **LottoNZ_Startup_Check**: Runs at PC startup to catch missed scrapes

#### Manual Testing

Test the scraper manually:
```bash
python dataScrape\mylotto_scraper.py
```

Test the scheduler logic:
```bash
python dataScrape\scheduler.py
```

## Project Structure

```
Backend/
├── dataScrape/
│   ├── ds.py                    # Legacy scraper (lottoresults.co.nz)
│   ├── ds_selenium.py           # Alternative legacy scraper
│   ├── mylotto_scraper.py       # New MyLotto scraper
│   ├── scheduler.py             # Scheduling logic
│   ├── last_run.json            # Tracks last scraper execution
│   └── scraper.log              # Rotating log file (auto-generated)
│
├── lotto-data/
│   ├── lotto_results.csv        # Raw lottery numbers
│   └── data.csv                 # Additional data
│
├── convert_to_json.py           # Converts data to JSON for frontend
├── datacleaner.py               # Data cleaning utilities
├── lotto_V3.py                  # Main analysis script
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration (create from .env.example)
├── .env.example                 # Environment configuration template
├── setup_scheduler.bat          # Setup weekly scheduled task
└── run_on_startup.bat           # Setup startup check task
```

## Scheduled Scraper Details

### How It Works

1. **Weekly Schedule**: The scraper runs every Sunday at 5:00 PM NZ time
2. **Missed Run Recovery**: If the PC is off during the scheduled time, the startup task will catch up when the PC restarts (if more than 7 days have passed)
3. **Duplicate Prevention**: The scheduler checks `last_run.json` to prevent running multiple times in the same week
4. **Logging**: All activity is logged to `dataScrape\scraper.log` with automatic rotation (max 10MB per file, keeps 5 backups)

### Managing Scheduled Tasks

View scheduled tasks:
```bash
schtasks /query /tn LottoNZ_Weekly_Scraper /v /fo LIST
schtasks /query /tn LottoNZ_Startup_Check /v /fo LIST
```

Run manually:
```bash
schtasks /run /tn LottoNZ_Weekly_Scraper
```

Delete tasks:
```bash
schtasks /delete /tn LottoNZ_Weekly_Scraper /f
schtasks /delete /tn LottoNZ_Startup_Check /f
```

### Logs

Check scraper logs:
```bash
type dataScrape\scraper.log
```

Check last run status:
```bash
type dataScrape\last_run.json
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `FIREFOX_PATH` | Path to Firefox executable (optional) | Auto-detected |
| `MYLOTTO_URL` | URL to scrape | `https://mylotto.co.nz/game-information` |
| `MAX_RETRIES` | Number of retry attempts | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Troubleshooting

### Scraper Not Running

1. Check if tasks are created:
   ```bash
   schtasks /query /tn LottoNZ_Weekly_Scraper
   ```

2. Check scraper log for errors:
   ```bash
   type dataScrape\scraper.log
   ```

3. Test scraper manually:
   ```bash
   python dataScrape\mylotto_scraper.py
   ```

### WebDriver Errors

- Ensure Firefox is installed
- Verify geckodriver is downl (geckodriver auto-downloads)
- Update Firefox to the latest version
- If Firefox is in a non-standard location, set `FIREFOX_PATH` in `.env`
- Check internet connection (needed to download geckodriver on first run)
### Permission Errors

- Run `setup_scheduler.bat` and `run_on_startup.bat` as Administrator if needed
- Check that Python has permission to write to the Backend directory

## Data Flow

```
MyLotto Scraper → lotto_results.csv → convert_to_json.py → results.json → Frontend
```

## License

See repository root for license information.
