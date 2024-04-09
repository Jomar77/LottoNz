import requests
from bs4 import BeautifulSoup
import csv
import os

# Simplified global variables
years = [str(year) for year in range(1987, 2024)]
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Utilize a session for requests
session = requests.Session()

def fetch_and_parse_url(url):
    """Fetches a webpage and returns its BeautifulSoup parsed object."""
    response = session.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    else:
        print(f"Failed to scrape {url}")
        return None

def extract_numbers_before_sep(soup):
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
from datetime import datetime

# def extract_date(soup):
#     """Extracts the draw date from the result-card title."""
#     title_tag = soup.find('h2', class_='result-card__title result-card__title--medium')
#     if not title_tag:
#         return None  # No date found
#     # Extract the date string
#     date_str = title_tag.text.strip()
#     print(f"Extracted date string: {date_str}")
#     # Parse the date
#     try:
#         draw_date = datetime.strptime(date_str, 'Lotto Result for %A, %d %B %Y')
#         return draw_date
#     except ValueError as e:
#         print(f"Failed to parse date: {e}")
#         return None  # If the date format doesn't match or parsing fails


def scrape_data(years, months):
    with open("lotto_results.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Year", "Month", "Day", "Numbers"])  # CSV Header
        
        for year in years:
            for month in months:
                url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
                soup = fetch_and_parse_url(url)
                if soup is None: continue
                
                # Iterate through each result card
                result_cards = soup.find_all('div', class_='result-card')
                for card in result_cards:
                    date_text = card.find('h2', class_='result-card__title--medium').text.strip()
                    try:
                        draw_date = datetime.strptime(date_text, "Lotto Result for %A, %d %B %Y")
                      # convert draw_date month to its numerical value
                      

                    except ValueError:
                        print(f"Failed to parse date from: {date_text}")
                        continue  # Skip this card if the date fails to parse
                    
                    numbers_list = extract_numbers_before_sep(card)  # Assume this function is adapted to work with a card's soup

                    # Write each row with the draw date and numbers
                    for i in range(0, len(numbers_list), 6):
                        writer.writerow([draw_date.year, draw_date.month, draw_date.day] + numbers_list[i:i+6])

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
