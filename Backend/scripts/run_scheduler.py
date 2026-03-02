"""
Cross-platform scheduler setup and runner
Replaces run_on_startup.bat and setup_scheduler.bat
"""
import sys
import subprocess
import platform
from pathlib import Path

def setup_windows_weekly_task():
    """Setup Windows Task Scheduler for weekly Sunday runs"""
    backend_dir = Path(__file__).parent.parent
    python_exe = sys.executable
    scheduler_script = backend_dir / "src" / "Scrapers" / "scheduler.py"
    
    if not scheduler_script.exists():
        print(f"❌ Scheduler script not found: {scheduler_script}")
        return False
    
    # Create weekly task (Sunday at 5:00 PM)
    task_name = "LottoNZ_Weekly_Scraper"
    cmd = [
        "schtasks", "/create",
        "/tn", task_name,
        "/tr", f'"{python_exe}" "{scheduler_script}"',
        "/sc", "weekly",
        "/d", "SUN",
        "/st", "17:00",
        "/rl", "HIGHEST",
        "/f"  # Force create/update
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Weekly task created: {task_name}")
        print(f"   Schedule: Every Sunday at 5:00 PM")
        print(f"   Script: {scheduler_script}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create weekly task: {e.stderr}")
        return False

def setup_windows_startup_task():
    """Setup Windows Task Scheduler for startup check"""
    backend_dir = Path(__file__).parent.parent
    python_exe = sys.executable
    scheduler_script = backend_dir / "src" / "Scrapers" / "scheduler.py"
    
    if not scheduler_script.exists():
        print(f"❌ Scheduler script not found: {scheduler_script}")
        return False
    
    # Create startup task with 2-minute delay
    task_name = "LottoNZ_Startup_Check"
    cmd = [
        "schtasks", "/create",
        "/tn", task_name,
        "/tr", f'"{python_exe}" "{scheduler_script}"',
        "/sc", "onstart",
        "/delay", "0002:00",
        "/rl", "HIGHEST",
        "/f"  # Force create/update
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Startup task created: {task_name}")
        print(f"   Trigger: At system startup (2 minute delay)")
        print(f"   Purpose: Catches missed weekly scrapes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create startup task: {e.stderr}")
        return False

def setup_windows_tasks():
    """Setup both Windows scheduled tasks"""
    print("=" * 70)
    print("Setting up Windows Task Scheduler")
    print("=" * 70)
    print()
    
    # Check Python
    print(f"Python: {sys.executable}")
    print(f"Version: {platform.python_version()}")
    print()
    
    # Setup weekly task
    weekly_success = setup_windows_weekly_task()
    print()
    
    # Setup startup task
    startup_success = setup_windows_startup_task()
    print()
    
    # Summary
    print("=" * 70)
    if weekly_success and startup_success:
        print("✅ Both tasks created successfully!")
        print()
        print("Task Management Commands:")
        print("  View weekly task:    schtasks /query /tn LottoNZ_Weekly_Scraper /v /fo LIST")
        print("  View startup task:   schtasks /query /tn LottoNZ_Startup_Check /v /fo LIST")
        print("  Run weekly task:     schtasks /run /tn LottoNZ_Weekly_Scraper")
        print("  Delete weekly task:  schtasks /delete /tn LottoNZ_Weekly_Scraper /f")
        print("  Delete startup task: schtasks /delete /tn LottoNZ_Startup_Check /f")
    else:
        print("⚠️  Some tasks failed to create")
        if not weekly_success:
            print("   - Weekly scraper task failed")
        if not startup_success:
            print("   - Startup check task failed")
    print("=" * 70)
    
    return weekly_success and startup_success

def setup_macos_launchd():
    """Setup macOS launchd"""
    print("⚠️  macOS launchd setup not yet implemented")
    print("   Run manually: python src/scrapers/scheduler.py")
    return False

def setup_linux_cron():
    """Setup Linux cron job"""
    print("⚠️  Linux cron setup not yet implemented")
    print("   Add to crontab: 0 8 * * * python /path/to/scheduler.py")
    return False

def run_scraper_now():
    """Run the scraper immediately (for testing)"""
    backend_dir = Path(__file__).parent.parent
    scheduler_script = backend_dir / "src" / "Scrapers" / "scheduler.py"
    
    if not scheduler_script.exists():
        print(f"❌ Scheduler script not found: {scheduler_script}")
        return False
    
    print(f"🔄 Running scraper: {scheduler_script}")
    print("=" * 70)
    try:
        subprocess.run([sys.executable, str(scheduler_script)], check=True)
        print("=" * 70)
        print("✅ Scraper completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("=" * 70)
        print(f"❌ Scraper failed: {e}")
        return False

def main():
    """Main entry point"""
    # Show usage if help requested
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("LottoNZ Scheduler Setup")
        print()
        print("Usage:")
        print("  python scripts/run_scheduler.py           # Setup scheduled tasks")
        print("  python scripts/run_scheduler.py --now     # Run scraper immediately")
        print("  python scripts/run_scheduler.py --help    # Show this help")
        print()
        print("Creates two scheduled tasks:")
        print("  1. Weekly scraper: Runs every Sunday at 5:00 PM")
        print("  2. Startup check: Runs at PC startup to catch missed scrapes")
        return
    
    # Run scraper now if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_scraper_now()
        return
    
    # Setup scheduled tasks
    os_type = platform.system()
    print()
    print(f"Operating System: {os_type}")
    print()
    
    if os_type == "Windows":
        setup_windows_tasks()
    elif os_type == "Darwin":
        setup_macos_launchd()
    elif os_type == "Linux":
        setup_linux_cron()
    else:
        print(f"❌ Unsupported OS: {os_type}")
    
    print()
    print("💡 Tips:")
    print("   Run now: python scripts/run_scheduler.py --now")
    print("   Get help: python scripts/run_scheduler.py --help")

if __name__ == "__main__":
    main()
