# Scripts Directory

Cross-platform automation scripts for LottoNZ backend.

## run_scheduler.py  
**Modern replacement for setup_scheduler.bat and run_on_startup.bat**

### What It Does

Creates **TWO** Windows scheduled tasks:

1. **LottoNZ_Weekly_Scraper**
   - Runs every **Sunday at 5:00 PM**
   - Executes `src/Scrapers/scheduler.py`
   - Same as `setup_scheduler.bat`

2. **LottoNZ_Startup_Check**
   - Runs at **PC startup** (2-minute delay)
   - Catches missed scrapes if PC was off on Sunday
   - Same as `run_on_startup.bat`

### Usage

```bash
# Setup both scheduled tasks
python scripts/run_scheduler.py

# Run scraper immediately (for testing)
python scripts/run_scheduler.py --now

# Show help
python scripts/run_scheduler.py --help
```

### Comparison

| Feature | .bat files | run_scheduler.py |
|---------|-----------|------------------|
| **Weekly Task** | ✅ setup_scheduler.bat | ✅ setup_windows_weekly_task() |
| **Startup Task** | ✅ run_on_startup.bat | ✅ setup_windows_startup_task() |
| **Run Now** | ❌ Must run task manually | ✅ --now flag |
| **Cross-platform** | ❌ Windows only | ✅ Ready for macOS/Linux |
| **Error handling** | ⚠️ Basic | ✅ Better error messages |
| **Path validation** | ❌ None | ✅ Checks if script exists |

### Task Details

#### Weekly Task
```
Task Name:  LottoNZ_Weekly_Scraper
Schedule:   Every Sunday at 17:00 (5:00 PM)
Script:     Backend/src/Scrapers/scheduler.py
Privilege:  HIGHEST
```

#### Startup Task
```
Task Name:  LottoNZ_Startup_Check
Schedule:   At system startup +2 minutes
Purpose:    Catch missed weekly scrapes
Script:     Backend/src/Scrapers/scheduler.py
Privilege:  HIGHEST
```

### Managing Tasks

```bash
# View tasks
schtasks /query /tn LottoNZ_Weekly_Scraper /v /fo LIST
schtasks /query /tn LottoNZ_Startup_Check /v /fo LIST

# Run manually
schtasks /run /tn LottoNZ_Weekly_Scraper

# Delete tasks
schtasks /delete /tn LottoNZ_Weekly_Scraper /f
schtasks /delete /tn LottoNZ_Startup_Check /f
```

### Next Steps

1. **Test the new Python script:**
   ```bash
   python scripts/run_scheduler.py
   ```

2. **Verify tasks were created:**
   ```bash
   schtasks /query /tn LottoNZ_Weekly_Scraper
   schtasks /query /tn LottoNZ_Startup_Check
   ```

3. **Test manual run:**
   ```bash
   python scripts/run_scheduler.py --now
   ```

4. **Delete old .bat files** (after confirming Python version works):
   ```bash
   del Scripts\setup_scheduler.bat
   del Scripts\run_on_startup.bat
   ```

### Why Replace .bat Files?

✅ **Single file** instead of two  
✅ **Cross-platform** ready (macOS/Linux stubs included)  
✅ **Better error handling** and validation  
✅ **Interactive testing** with `--now` flag  
✅ **Cleaner** Python code instead of batch scripts  
✅ **Maintainable** - easier to extend/modify  

### Troubleshooting

**Error: Script not found**
```
❌ Scheduler script not found: Backend/src/Scrapers/scheduler.py
```
→ Make sure you're running from the Backend directory  
→ Check that scheduler.py exists in src/Scrapers/

**Error: Permission denied**
```
❌ Failed to create task: Access is denied
```
→ Run terminal as Administrator  
→ Or adjust task privileges

**Task not running on schedule**
→ Check Windows Task Scheduler GUI: `taskschd.msc`  
→ Look for errors in task history  
→ Check `src/Scrapers/scraper.log` for execution logs
