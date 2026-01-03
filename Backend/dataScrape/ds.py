from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import csv
import os
import time

# Simplified global variables
years = [str(year) for year in range(1997, 2025)]
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Set up Selenium WebDriver for Firefox
firefox_options = Options()
firefox_options.binary_location="C:\\Program Files\\Mozilla Firefox\\firefox.exe"
firefox_options.add_argument("--headless")  # Run in headless mode (no GUI)
service = Service(executable_path="C:\\Users\\jomna\\Downloads\\geckodriver.exe")
driver = webdriver.Firefox(service=service, options=firefox_options)

def fetch_and_parse_url(url):
    """Fetches a webpage using Selenium and returns its BeautifulSoup parsed object."""
    driver.get(url)
    time.sleep(3)  # Adjust sleep time as needed for the page to load completely
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

def extract_numbers_before_separator(soup):
    """Finds and extracts the 6 numbers preceding each 'draw-result__sep' separator."""
    separators = soup.find_all('li', class_='draw-result__sep')
    
    all_numbers = []
    
    for sep in separators:
        current = sep.previous_sibling
        numbers = []
        
        # Collect the six numbers preceding the current separator
        while current and len(numbers) < 6:
            if current.name == 'li' and 'draw-result__ball' in current.get('class', []):
                numbers.insert(0, current.text.strip())  # Prepend to maintain order
            current = current.previous_sibling
            
        if numbers:  # Ensure only non-empty lists are added
            all_numbers.extend(numbers)  # Flatten the list to match previous logic
            
    return all_numbers

def scrape_data(years, months):
    with open("lotto_results.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        
        for year in years:
            for month in months:
                url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
                soup = fetch_and_parse_url(url)
                if soup is None:
                    print(f"Failed to scrape {url}")
                    continue
                
                # Iterate through each result card
                result_cards = soup.find_all('div', class_='result-card')
                for card in result_cards:
                    numbers_list = extract_numbers_before_separator(card)  
                    for i in range(0, len(numbers_list), 6):
                        writer.writerow(numbers_list[i:i+6])
                    
                    print(f"Scraped {month} {year}: {numbers_list[i:i+6]}")

def main():
    # Ensure the output file is fresh
    output_file = "lotto_results.csv"
    if os.path.exists(output_file):
        os.remove(output_file)

    scrape_data(years, months)
    print("Scraping complete. Data saved to lotto_results.csv.")
    driver.quit()  # Close the Selenium WebDriver

if __name__ == "__main__":
    main()
