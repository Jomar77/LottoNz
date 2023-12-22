import requests
from bs4 import BeautifulSoup

import os

# Specify the file name
file_name = ["powerball.csv", "lotto.csv", "output.csv"]

# Check if file exists then delete it
for i in range(0, len(file_name)):
    if os.path.exists(file_name[i]):
        os.remove(file_name[i])
        print(f"{file_name[i]} has been deleted.")
    else:
        print("The file does not exist.")

# create a loop for month names
for month in range(12):
    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]

    # for year in range(5):
    #         years = ['2019', '2020', '2021', '2022', '2023']
    #     # URL of the website you want to scrape
    #         url = "http://lottoresults.co.nz/lotto/" + months[month] +"-" + years[year]
    # URL of the website you want to scrape
    url = "http://lottoresults.co.nz/lotto/" + months[month] + "-2023"

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    article_titles = soup.find_all("li", class_="draw-result__ball")
    list = []
    # Loop through the article titles and add them to the list
    for title in article_titles:
        list.append(title.text.strip())

    # seperate the list into tuples of 6
    list = [tuple(list[i : i + 6]) for i in range(0, len(list), 6)]

    # write it in a csv file
    import csv

    with open("lotto.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(list)

    pball_list=[]
    article_titles = soup.find_all("li", class_="draw-result__ball")
    # Loop through the article titles and add every 12th item starting from index 7 to the list
    for i in range(7, len(article_titles), 12):
        pball_list.append(article_titles[i].text.strip())

    with open("powerball.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(pball_list)


import csv

input_file = "lotto.csv"
output_file = "output.csv"

with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for i, row in enumerate(reader, start=1):
        if i % 2 == 0:
            # Delete content from even-numbered lines
            row = [""] * len(row)

        # Check if any element in the row is non-empty
        if any(cell.strip() for cell in row):
            writer.writerow(row)

print("Empty lines removed from even-numbered lines.")
