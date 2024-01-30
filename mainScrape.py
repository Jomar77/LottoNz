import dataScrape as ds

# Path: dataScrape.py
import requests
from bs4 import BeautifulSoup
import os
import csv

#main function
if __name__ == "__main__":
    ds.delete_file("output.csv")
    ds.scrape_data_bfr()
    ds.scrape_data()
    ds.scrape_data_ovr()
    print("Done")