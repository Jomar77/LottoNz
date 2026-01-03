import requests
from bs4 import BeautifulSoup
import csv
import os
import sys

# Simplified global variables
years = [str(year) for year in range(2002, 2008)]
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Utilize a session for requests
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
}
session.headers.update(headers)

def fetch_and_parse_url(url):
    """Fetches a webpage and returns its BeautifulSoup parsed object."""
    response = session.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    else:
        print(f"Failed to scrape {url}")
        return None

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
                    sys.exit()
                
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

if __name__ == "__main__":
    main()
