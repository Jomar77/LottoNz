"""
Scheduler Wrapper for MyLotto Scraper
Manages scheduling logic, tracks last run, and determines if scraping is needed
"""

import json
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import mylotto_scraper

# File paths
LAST_RUN_FILE = SCRIPT_DIR / 'last_run.json'
LOG_FILE = SCRIPT_DIR / 'scraper.log'

# Configure logging with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Rotating file handler (max 10MB, keep 5 backups)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class SchedulerManager:
    """Manages scraper scheduling and execution tracking"""
    
    def __init__(self):
        self.last_run_data = self.load_last_run()
    
    def load_last_run(self):
        """Load last run data from JSON file"""
        try:
            if LAST_RUN_FILE.exists():
                with open(LAST_RUN_FILE, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded last run data: {data}")
                    return data
            else:
                logger.info("No previous run data found")
                return None
        except Exception as e:
            logger.error(f"Error loading last run data: {e}")
            return None
    
    def save_last_run(self, status, error_message=None):
        """Save last run data to JSON file"""
        try:
            now = datetime.now()
            data = {
                'last_attempt': now.isoformat(),
                'status': status,
                'error_message': error_message
            }
            
            if status == 'success':
                data['last_successful_run'] = now.isoformat()
            elif self.last_run_data and 'last_successful_run' in self.last_run_data:
                # Preserve last successful run if current attempt failed
                data['last_successful_run'] = self.last_run_data['last_successful_run']
            
            with open(LAST_RUN_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved run data: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving last run data: {e}")
            return False
    
    def should_run_scraper(self):
        """Determine if scraper should run based on last execution"""
        try:
            now = datetime.now()
            
            # If no previous run, we should run
            if not self.last_run_data or 'last_successful_run' not in self.last_run_data:
                logger.info("No previous successful run found. Should run scraper.")
                return True
            
            # Parse last successful run timestamp
            last_run_str = self.last_run_data['last_successful_run']
            last_run = datetime.fromisoformat(last_run_str)
            
            # Calculate days since last run
            days_since_run = (now - last_run).days
            
            logger.info(f"Last successful run: {last_run_str} ({days_since_run} days ago)")
            
            # Should run if more than 7 days have passed
            if days_since_run >= 7:
                logger.info(f"More than 7 days since last run. Should run scraper.")
                return True
            
            # Check if it's Sunday after 5 PM and we haven't run this week
            if now.weekday() == 6 and now.hour >= 17:  # Sunday = 6
                # Check if last run was before this Sunday
                days_until_sunday = (6 - last_run.weekday()) % 7
                next_sunday_after_last_run = last_run + timedelta(days=days_until_sunday)
                
                if now.date() >= next_sunday_after_last_run.date():
                    logger.info("It's Sunday after 5 PM and we haven't run this week. Should run scraper.")
                    return True
            
            logger.info("Scraper already ran recently. Skipping.")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if scraper should run: {e}")
            # When in doubt, don't run to avoid duplicate scraping
            return False
    
    def run(self):
        """Main scheduling logic"""
        logger.info("=== Scheduler started ===")
        
        try:
            # Check if we should run
            if not self.should_run_scraper():
                logger.info("Scraper not scheduled to run at this time.")
                return 0
            
            logger.info("Executing scraper...")
            
            # Execute scraper
            scraper = mylotto_scraper.MyLottoScraper()
            success = scraper.scrape()
            
            # Save run status
            if success:
                self.save_last_run('success')
                logger.info("=== Scraper completed successfully ===")
                return 0
            else:
                self.save_last_run('failed', 'Scraper returned False')
                logger.error("=== Scraper failed ===")
                return 1
                
        except Exception as e:
            error_msg = f"Exception during scraper execution: {e}"
            logger.error(error_msg)
            self.save_last_run('failed', error_msg)
            return 1


def main():
    """Main entry point"""
    scheduler = SchedulerManager()
    exit_code = scheduler.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
