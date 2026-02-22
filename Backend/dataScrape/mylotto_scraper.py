"""
MyLotto.co.nz Web Scraper
Downloads lottery data Excel file from mylotto.co.nz/game-information
Targets "Draw results (all games)" document and converts to JSON
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import os
import sys
import time
import logging
import glob
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FIREFOX_PATH = os.getenv('FIREFOX_PATH', None)  # Optional: set if Firefox in non-standard location
MYLOTTO_URL = os.getenv('MYLOTTO_URL', 'https://mylotto.co.nz/game-information')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))
DOWNLOAD_TIMEOUT = 300  # 5 minutes max for download
GIT_COMMIT_DELAY = int(os.getenv('GIT_COMMIT_DELAY', '300'))  # 5 minutes delay before commit
ENABLE_AUTO_COMMIT = os.getenv('ENABLE_AUTO_COMMIT', 'true').lower() == 'true'

# File paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / 'lotto-data'
EXCEL_FILE = DATA_DIR / 'december.xlsx'
DOWNLOADS_DIR = Path.home() / 'Downloads'
CONVERT_SCRIPT = BACKEND_DIR / 'convert_to_json.py'
RESULTS_JSON = REPO_DIR / 'Frontend' / 'public' / 'results.json'


class MyLottoScraper:
    """Scraper for mylotto.co.nz lottery data"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Initialize Selenium WebDriver with Firefox"""
        try:
            firefox_options = Options()
            
            # Set Firefox binary location if specified
            if FIREFOX_PATH:
                firefox_options.binary_location = FIREFOX_PATH
                logger.info(f"Using Firefox from: {FIREFOX_PATH}")
            
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            
            # Set download preferences
            firefox_options.set_preference("browser.download.folderList", 2)
            firefox_options.set_preference("browser.download.dir", str(DOWNLOADS_DIR))
            firefox_options.set_preference("browser.download.useDownloadDir", True)
            firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel")
            firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
            firefox_options.set_preference("pdfjs.disabled", True)
            
            # Use webdriver-manager to automatically download and manage geckodriver
            logger.info("Setting up geckodriver (will auto-download if needed)...")
            service = FirefoxService(GeckoDriverManager().install())
            
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            self.driver.set_page_load_timeout(30)
            logger.info("WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error("Make sure Firefox is installed on your system")
            return False
    
    def fetch_page(self, url, retry_count=0):
        """Fetch webpage with retry logic"""
        try:
            logger.info(f"Fetching URL: {url} (attempt {retry_count + 1}/{MAX_RETRIES})")
            self.driver.get(url)
            
            # Wait for the page to load - look for document group elements
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lnz-document-group__document"))
            )
            
            time.sleep(2)  # Additional wait for dynamic content
            logger.info("Page loaded successfully")
            return True
            
        except TimeoutException:
            logger.warning(f"Timeout loading page (attempt {retry_count + 1})")
            if retry_count < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                return self.fetch_page(url, retry_count + 1)
            else:
                logger.error("Max retries reached. Giving up.")
                return False
                
        except WebDriverException as e:
            logger.error(f"WebDriver exception: {e}")
            if retry_count < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                return self.fetch_page(url, retry_count + 1)
            return False
    
    def find_and_click_draw_results_link(self):
        """Find and click the download link for 'Draw results (all games)' Excel file"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all h2 tags on the page
            h2_tags = soup.find_all('h2', class_='lnz-document-group__title')
            logger.info(f"Found {len(h2_tags)} h2 title elements")
            
            for h2 in h2_tags:
                h2_text = h2.get_text(strip=True)
                logger.info(f"Checking h2: {h2_text}")
                
                # Check if this h2 contains "Draw results (all games)"
                if "Draw results" in h2_text and "all games" in h2_text:
                    logger.info(f"Found matching h2: {h2_text}")
                    
                    # Find the parent container
                    parent = h2.find_parent('div', class_='lnz-document-group')
                    if not parent:
                        logger.warning("Could not find parent lnz-document-group div")
                        continue
                    
                    # Find the document link within this group
                    doc_div = parent.find('div', class_='lnz-document-group__document')
                    if not doc_div:
                        logger.warning("Could not find lnz-document-group__document div")
                        continue
                    
                    # Find the <a> tag with the download link
                    link = doc_div.find('a', href=True)
                    if link and link['href']:
                        download_url = link['href']
                        
                        # Get file info
                        file_name_elem = doc_div.find('p', class_='lnz-document-group__document-title')
                        file_name = file_name_elem.get_text(strip=True) if file_name_elem else "Unknown"
                        
                        logger.info(f"Found download link: {download_url}")
                        logger.info(f"File name: {file_name}")
                        
                        # Now find and click the actual element using Selenium
                        try:
                            # Find all links on the page
                            link_elements = self.driver.find_elements(By.TAG_NAME, 'a')
                            
                            for link_elem in link_elements:
                                try:
                                    href = link_elem.get_attribute('href')
                                    if href and href == download_url:
                                        logger.info(f"Clicking download link...")
                                        link_elem.click()
                                        return True
                                except:
                                    continue
                            
                            logger.error("Found URL but couldn't click the element")
                            return False
                            
                        except Exception as e:
                            logger.error(f"Error clicking element: {e}")
                            return False
            
            logger.error("Could not find 'Draw results (all games)' section")
            return False
            
        except Exception as e:
            logger.error(f"Error finding draw results link: {e}")
            return False
    
    def wait_for_download(self):
        """Wait for Excel file download to complete"""
        try:
            # Get list of files before download
            before_files = set(glob.glob(str(DOWNLOADS_DIR / "*.xlsx")))
            logger.info(f"Files in Downloads before: {len(before_files)}")
            
            # Wait for new file to appear
            logger.info("Waiting for download to complete...")
            start_time = time.time()
            downloaded_file = None
            
            while time.time() - start_time < DOWNLOAD_TIMEOUT:
                time.sleep(2)
                
                # Check for new xlsx files
                current_files = set(glob.glob(str(DOWNLOADS_DIR / "*.xlsx")))
                new_files = current_files - before_files
                
                # Filter out .part files (incomplete downloads)
                complete_files = [f for f in new_files if not f.endswith('.part')]
                
                if complete_files:
                    downloaded_file = complete_files[0]
                    logger.info(f"Download completed: {downloaded_file}")
                    break
                
                # Check for .part files (download in progress)
                part_files = glob.glob(str(DOWNLOADS_DIR / "*.xlsx.part"))
                if part_files:
                    logger.debug("Download in progress...")
            
            if not downloaded_file:
                logger.error("Download timeout - file did not appear in Downloads folder")
                return None
            
            # Verify file exists and has content
            file_size = os.path.getsize(downloaded_file)
            logger.info(f"Downloaded file size: {file_size} bytes")
            
            if file_size == 0:
                logger.error("Downloaded file is empty")
                return None
            
            return downloaded_file
            
        except Exception as e:
            logger.error(f"Error waiting for download: {e}")
            return None
    
    def move_and_convert_file(self, downloaded_file):
        """Move downloaded file to lotto-data folder and convert to JSON"""
        try:
            # Ensure data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Move/copy file to december.xlsx
            logger.info(f"Moving file from {downloaded_file} to {EXCEL_FILE}")
            shutil.move(downloaded_file, EXCEL_FILE)
            logger.info(f"File saved as: {EXCEL_FILE}")
            
            # Run the conversion script
            logger.info(f"Running conversion script: {CONVERT_SCRIPT}")
            result = subprocess.run(
                [sys.executable, str(CONVERT_SCRIPT)],
                capture_output=True,
                text=True,
                cwd=str(BACKEND_DIR)
            )
            
            if result.returncode == 0:
                logger.info("Conversion successful:")
                logger.info(result.stdout)
                return True
            else:
                logger.error("Conversion failed:")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"Error moving/converting file: {e}")
            return False
    
    def git_commit_and_push(self):
        """Commit and push changes to GitHub repository"""
        try:
            logger.info("=== Starting Git commit process ===")
            
            # Change to repository directory
            os.chdir(REPO_DIR)
            logger.info(f"Working directory: {REPO_DIR}")
            
            # Check git status
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=str(REPO_DIR)
            )
            
            if not result.stdout.strip():
                logger.info("No changes to commit")
                return True
            
            logger.info(f"Changes detected:\n{result.stdout}")
            
            # Add the updated files
            files_to_add = [
                'Backend/lotto-data/december.xlsx',
                'Frontend/public/results.json'
            ]
            
            for file in files_to_add:
                file_path = REPO_DIR / file
                if file_path.exists():
                    logger.info(f"Adding file: {file}")
                    result = subprocess.run(
                        ['git', 'add', file],
                        capture_output=True,
                        text=True,
                        cwd=str(REPO_DIR)
                    )
                    if result.returncode != 0:
                        logger.error(f"Failed to add {file}: {result.stderr}")
                else:
                    logger.warning(f"File not found: {file}")
            
            # Commit with timestamp
            commit_message = f"Auto-update lottery data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Committing with message: {commit_message}")
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                text=True,
                cwd=str(REPO_DIR)
            )
            
            if result.returncode != 0:
                # Check if it's just "nothing to commit"
                if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                    logger.info("Nothing to commit (files unchanged)")
                    return True
                logger.error(f"Failed to commit: {result.stderr}")
                return False
            
            logger.info(f"Commit successful: {result.stdout}")
            
            # Push to remote
            logger.info("Pushing to GitHub...")
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                capture_output=True,
                text=True,
                cwd=str(REPO_DIR)
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to push: {result.stderr}")
                return False
            
            logger.info(f"Push successful: {result.stdout}")
            logger.info("=== Git commit process completed ===")
            return True
            
        except FileNotFoundError:
            logger.error("Git is not installed or not in PATH")
            return False
        except Exception as e:
            logger.error(f"Error during git commit: {e}")
            return False
    
    def scrape(self):
        """Main scraping method"""
        try:
            logger.info("=== Starting MyLotto scraper ===")
            
            # Setup driver
            if not self.setup_driver():
                logger.error("Failed to setup WebDriver")
                return False
            
            # Fetch page
            if not self.fetch_page(MYLOTTO_URL):
                logger.error("Failed to fetch page")
                return False
            
            # Find and click the download link
            if not self.find_and_click_draw_results_link():
                logger.error("Failed to find and click download link")
                return False
            
            # Wait for the download to complete
            downloaded_file = self.wait_for_download()
            if not downloaded_file:
                logger.error("Failed to download Excel file")
                return False
            
            # Move and convert the file
            if not self.move_and_convert_file(downloaded_file):
                logger.error("Failed to convert file to JSON")
                return False
            
            logger.info("=== Scraping completed successfully ===")
            
            # Auto-commit to GitHub if enabled
            if ENABLE_AUTO_COMMIT:
                logger.info(f"Waiting {GIT_COMMIT_DELAY} seconds before committing to GitHub...")
                time.sleep(GIT_COMMIT_DELAY)
                
                if not self.git_commit_and_push():
                    logger.warning("Git commit failed, but scraping was successful")
                    # Don't return False - scraping itself was successful
            else:
                logger.info("Auto-commit is disabled")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()


def main():
    """Main entry point"""
    scraper = MyLottoScraper()
    success = scraper.scrape()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
