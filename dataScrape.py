import requests
from bs4 import BeautifulSoup
import os
import csv

def delete_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"{file_name} has been deleted.")
    else:
        print("The file does not exist.")

def scrape_data():
    years = ['2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023','2024','2025']
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    for year in years:
        if year == "2001":
            months = months[1:]
        # if 2024, only scrape up to january
        if year == "2024":
            months = months[:1]
        for month in months:
            url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            article_titles = soup.find_all("li", class_="draw-result__ball")
            numbers_list = [title.text.strip() for title in article_titles]

            numbers_list = reversed([tuple(numbers_list[i : i + 6]) for i in range(0, len(numbers_list), 6)])

            with open("lotto.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(numbers_list)
                
def scrape_data_ovr(year,month):
    url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    article_titles = soup.find_all("li", class_="draw-result__ball")
    numbers_list = [title.text.strip() for title in article_titles]

    numbers_list = reversed([tuple(numbers_list[i : i + 6]) for i in range(0, len(numbers_list), 6)])
    
    with open("lotto.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(numbers_list)

       
def remove_empty_lines(input_file, output_file):
    with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for i, row in enumerate(reader, start=1):
            if i % 2 == 1:
                row = [""] * len(row)

            if any(cell.strip() for cell in row):
                writer.writerow(row)

    print("Empty lines removed from even-numbered lines.")

# Specify the file names
file_names = ["powerball.csv", "lotto.csv", "output.csv"]

# Delete existing files
for file_name in file_names:
    delete_file(file_name)

# Create a loop for year and month names


scrape_data()
scrape_data_ovr("2024","january")

    
input_file = "lotto.csv"
output_file = "output.csv"

remove_empty_lines(input_file, output_file)
