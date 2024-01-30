import requests
from bs4 import BeautifulSoup
import os
import csv

years = [
    "2001",
    "2002",
    "2003",
    "2004",
    "2005",
    "2006",
    "2007",
    "2008",
    "2009",
    "2010",
    "2011",
    "2012",
    "2013",
    "2014",
    "2015",
    "2016",
    "2017",
    "2018",
    "2019",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
]
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


def delete_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"{file_name} has been deleted.")
    else:
        print("The file does not exist.")


class scrapeChild():
    def scrape_data(years, months):
        for year in years:
            months_to_scrape = months
            if year == "2001":
                months_to_scrape = months[2:]
            elif year == "2024":
                months_to_scrape = months[:1]  # only scrape the first month of 2024
            for month in months_to_scrape:
                url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")

                article_titles = soup.find_all("li", class_="draw-result__ball")
                numbers_list = [title.text.strip() for title in article_titles]

                numbers_list = reversed(
                    [
                        tuple(numbers_list[i : i + 6])
                        for i in range(0, len(numbers_list), 6)
                    ]
                )

                with open("lotto.csv", "a", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(numbers_list)


def scrape_data_bfr():
    years = ["1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000"]
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
    for year in years:
        if year == "2001":
            months = months[1:]
        # if 2024, only scrape up to january
        for month in months:
            url = f"http://lottoresults.co.nz/lotto/{month}-{year}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            article_titles = soup.find_all("li", class_="draw-result__ball")
            numbers_list = [title.text.strip() for title in article_titles]

            # numbers_list = reversed(
            #     [tuple(numbers_list[i : i + 6]) for i in range(0, len(numbers_list), 6)]
            # )
            numbers_list = [
                tuple(numbers_list[i : i + 6]) for i in range(0, len(numbers_list), 11)
            ]

            with open("output_bfr.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(numbers_list)


def scrape_data_main():
    scrapeChild.scrape_data(years, months)

    input_file = "lotto.csv"
    output_file = "output.csv"

    remove_empty_lines(input_file, output_file)
    scrape_data_bfr()
    
    merge_csv("output_bfr.csv", "output.csv", "output_merged.csv")
    

def merge_csv(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2, open(output_file, 'w', newline='') as output:
        reader1 = csv.reader(f1)
        reader2 = csv.reader(f2)
        writer = csv.writer(output)

        # Merge the rows
        for row in reader1:
            writer.writerow(row)
        for row in reader2:
            writer.writerow(row)


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


def main():
    # Specify the file names
    file_names = ["lotto.csv", "output.csv", "output_bfr.csv", "output_merged.csv"]

    # Delete existing files
    for file_name in file_names:
        delete_file(file_name)

    scrape_data_main()


if __name__ == "__main__":
    main()
