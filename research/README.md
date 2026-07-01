# LottoNZ Backend

Python backend for lottery number generation and data scraping.

## 🏗️ Project Structure

```
Backend/
├── src/
│   ├── Core/           # Business logic
│   │   └── lotto_generator.py
│   ├── Scrapers/       # Web scrapers
│   │   ├── mylotto_scraper.py
│   │   └── scheduler.py
│   └── Utils/          # Helper functions
│       ├── data_cleaner.py
│       ├── file_search.py
│       └── json_converter.py
├── tests/              # Unit tests
├── scripts/            # Setup and deployment scripts
│   └── run_scheduler.py
└── requirements.txt    # Python dependencies
```

## ⚙️ Setup

### Prerequisites
- Python 3.8 or higher
- Firefox browser (for web scraping)

### 1. Create Virtual Environment (at ROOT level)

⚠️ **IMPORTANT**: Create `.venv` at the **root** level (LottoNZ/), NOT in Backend/

```bash
# Navigate to project root
cd LottoNZ

# Create virtual environment
python -m venv .venv

# Activate it:
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
cd Backend
pip install -r requirements.txt

# Dev dependencies (for testing)
pip install -r requirements-dev.txt
```

### 3. Configure Environment
```bash
copy .env.example .env
# Edit .env with your credentials if needed
```

## 🚀 Usage

### Run Scraper
```bash
# One-time run
python -m src.Scrapers.scheduler

# Or use the helper script
python scripts/run_scheduler.py --now
```

### Setup Scheduled Scraping

#### Cross-Platform (Recommended)
```bash
python scripts/run_scheduler.py
```

#### Windows Legacy (using .bat files)
```bash
# These still work but will be deprecated
Scripts\setup_scheduler.bat
```

### Generate Lotto Numbers
```bash
python -m src.Core.lotto_generator
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_lotto_generator.py
```

## 📝 Development

### Adding New Features
1. Create module in appropriate folder (Core/Scrapers/Utils)
2. Add corresponding test in `tests/`
3. Update `__init__.py` if creating new module
4. Run tests before committing

### Code Style
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all public functions/classes

## 🔧 Troubleshooting

### Virtual Environment Issues

**Error**: "Unable to handle ... .venv\Scripts\python.exe"

**Solution**: 
1. Delete `.venv` from Backend folder if it exists
2. Create `.venv` at root level: `LottoNZ/.venv` (not Backend/.venv)
3. Reload VS Code:
   - Press `Ctrl+Shift+P`
   - Type "Developer: Reload Window"
4. Select Python interpreter:
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose the one with `.venv` in the path

### Import Errors

Make sure you're running from the Backend directory with `-m` flag:
```bash
cd Backend
python -m src.Core.lotto_generator  # ✅ Correct
# NOT: python src/Core/lotto_generator.py  # ❌ Wrong
```

### Scraper Errors

```bash
# Check logs
type src\Scrapers\scraper.log

# Check last run status
type src\Scrapers\last_run.json

# Test manually
python -m src.Scrapers.mylotto_scraper
```

## 📂 Data

Data files live in `../Data/` (outside Backend):
- `raw/` - Scraped data from MyLotto NZ
- `processed/` - Cleaned data ready for analysis

## 🛠️ Tech Stack

- **Python 3.8+**
- **Selenium** - Web scraping
- **Pandas** - Data processing  
- **Schedule** - Task scheduling
- **pytest** - Testing framework

## 📋 Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `FIREFOX_PATH` | Path to Firefox executable | Auto-detected |
| `MYLOTTO_URL` | URL to scrape | `https://mylotto.co.nz/game-information` |
| `MAX_RETRIES` | Number of retry attempts | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🚧 TODO

- [ ] Rename folders to lowercase (Core → core, Utils → utils, Scrapers → scrapers)
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Improve test coverage (>80%)
- [ ] Add FastAPI REST endpoints
- [ ] Docker containerization
- [ ] Database integration (PostgreSQL/SQLite)

## 📖 Documentation

- See `../Docs/` for setup guides and reference docs
- Each module has inline docstrings
- Run `pydoc` for API documentation

## 📄 License

See repository root for license information.
