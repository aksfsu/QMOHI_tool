from bs4 import BeautifulSoup
from os.path import exists
from os import makedirs
import re

import asyncio
import pyppeteer
import wget

# Config constants
MEDLINE_URL = "https://medlineplus.gov"
OUTPUT_DIR = "./health_topics"

# Access websites based on the given URL
async def get_html_from_url(url):
    # print(url)
    browser = await pyppeteer.launch({
        'args': ['--no-sandbox', '--disable-dev-shm-usage']
    })
    page = await browser.newPage()
    await page.goto(url)
    html = await page.content()
    await browser.close()
    return html

# Collect internal links within Medline
def get_internal_links():
    if not exists(OUTPUT_DIR):
        makedirs(OUTPUT_DIR)

    # Get the HTML based on URL
    html = asyncio.get_event_loop().run_until_complete(get_html_from_url("https://medlineplus.gov/all_healthtopics.html"))
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    visited_urls = []
    for a in soup.find_all('a', href=True):
        # Get the URL from the a tag
        link = a['href'].strip()
        # print(link)
        
        # Avoid revisiting the same URL
        if link in visited_urls:
            continue
        visited_urls.append(link)
        
        # Check if the URL is valid
        if not link:
            continue
        elif MEDLINE_URL not in link:
            continue
        elif re.match('./', link):
            link = MEDLINE_URL + link[2:]
        
        # Download the HTML file from the URL
        try:
            wget.download(url=link, out=OUTPUT_DIR)
        except:
            continue

# Get the summary text from an HTML file
def get_text_from_html(input_file_path, output_file_path):
    with open(input_file_path, "r") as input_file:
        html = input_file.read()        
        soup = BeautifulSoup(html, 'html.parser')
        summary = soup.find(id="topic-summary")
        if summary:
            text = summary.get_text(separator=" ", strip=True)
            with open(output_file_path, "w") as output_file:
                output_file.write(text)

# Get the summary text from all the MedlinePlus health topics
def get_documents():
    input_dir = "./health_topics"
    input_files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
    output_dir = "./health_topics_summary"
    if not exists(output_dir):
        makedirs(output_dir)
    for input_file in input_files:
        get_text_from_html(join(input_dir, input_file), join(output_dir, re.sub(".html", ".txt", input_file)))

def main():
    # Get all the links to the MedlinePlus health topics
    get_internal_links()
    # Get the summary text in the URL
    get_documents()

if __name__ == "__main__":
    main()