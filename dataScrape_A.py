import requests
from bs4 import BeautifulSoup

#create a loop for month names

# URL of the website you want to scrape

url = input("Enter the url: ")

# Send an HTTP GET request to the URL
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all the article titles on the page
article_titles = soup.find_all('strong' )

# Loop through the article titles and print them
list = []
for title in article_titles:
    # create list and seperate the list into tuples of 6
    list.append(title.text.strip())

for i in range(0, len(list)):
    print(list[i])