import requests
from bs4 import BeautifulSoup

#create a loop for month names
for month in range(12):
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august','september', 'october', 'november', 'december']

    # URL of the website you want to scrape
    url = "http://lottoresults.co.nz/lotto/" + months[month] +"-2023"

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the article titles on the page
    article_titles = soup.find_all('li', class_="draw-result__ball" )

    # Loop through the article titles and print them
    list = []
    for title in article_titles:
        # create list and seperate the list into tuples of 6
        list.append(title.text.strip())

   #seperate the list into tuples of 6
    list = [tuple(list[i:i+6]) for i in range(0, len(list), 6)]

    #write it in a csv file
    import csv
    with open('lotto.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(list)

    #remove the even lines
import csv

input_file = 'lotto.csv'
output_file = 'output.csv'

with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    for i, row in enumerate(reader, start=1):
        if i % 2 == 0:
            # Delete content from even-numbered lines
            row = [''] * len(row)
            
        # Check if any element in the row is non-empty
        if any(cell.strip() for cell in row):
            writer.writerow(row)

print("Empty lines removed from even-numbered lines.")

