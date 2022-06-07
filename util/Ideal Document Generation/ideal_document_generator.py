from bs4 import BeautifulSoup
from os.path import join, dirname
from os import makedirs
import sys
import re

import config 
import cse_handler

import asyncio
import pyppeteer

# Config constants
API_KEY = config.MY_API_KEY
CSE_ID = config.MY_CSE_ID
MEDLINE_URL = "https://medlineplus.gov"
DEPTH = 2 # (>= 1)
OUTPUT_DIR = "./output"

# Experimental terms
EXPERIMENTAL_TERMS = [
    "Accidental Injury", #
    "Broken Limbs",
    "First Aid", #
    "Allergy", #
    "Asthma",
    "Flu",
    "Cold", #
    "Standard Immunizations",
    "Vaccines", #
    "Tobacco",
    "Alcohol",
    "Drug Issues",
    "Mental Health Depression",
    "Anxiety",
    "Stress",
    "Time Management",
    "Abortion",
    "Medicated Abortion",
    "Sexual Harrassment",
    "Abuse",
    "Assault",
    "Violence",
    "Body Image",
    "Nutrition",
    "Obesity",
    "HIV",
    "STD",
    "Sexual Health",
    "Safe Sex",
    "Urinary Tract Infections",
]

# Access websites based on the given URL
async def get_html_from_url(url):
    print(url)
    browser = await pyppeteer.launch({
        'args': ['--no-sandbox', '--disable-dev-shm-usage']
    })
    page = await browser.newPage()
    await page.goto(url)
    html = await page.content()
    await browser.close()
    return html

# Collect internal links within Medline
def get_internal_links(soup, parent_url):
    internal_links = []
    for a in soup.findAll('a', href=True):
        link = a['href']
        if not link:
            print("No URL assigned")
        elif MEDLINE_URL in link:
            m = re.search("/", parent_url[::-1])
            if m.start() > 0:
                internal_links.append(link)
        elif re.match('./', link):
            m = re.search("/", parent_url[::-1])
            if m.start() > 0:
                parent_url = parent_url[:-m.start()]
                abs_link = parent_url + link[2:]
                #print(f'Abs Link: {abs_link}')
                internal_links.append(abs_link)
    return internal_links

# Get text data and export in the output file
def get_document(output_file, url, depth, visited_urls):
    if depth == 0:
        return

    # Get the HTML based on URL
    html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve information only once from the same websites
    urls = []
    if url not in visited_urls:
        visited_urls.append(url)

        text = ""
        # The term has a dedicated "Medical Encyclopedia" page
        if "ency" in url:
            # Get the summary element
            summary = soup.find(id="ency_summary")
            if summary:
                # Collect internal links
                urls.extend(get_internal_links(summary, url))
                # Get the text data
                text += summary.get_text(separator=" ", strip=True)
                # Get the sections
                sections = summary.parent.find_all('div', {'class': 'section'})
            else:
                return visited_urls
            if sections:
                for section in sections:
                    section_body = section.find('div', {'id': re.compile(r'section-\d+')})
                    if section_body:
                        # Collect internal links
                        urls.extend(get_internal_links(section_body, url))
                        # Get the text data
                        text += section_body.get_text(separator=" ", strip=True)

        # The term has a dedicated "Lab Tests" page
        elif "lab-tests" in url:
            # Get the main description element
            sections = soup.find_all('div', {'class': 'mp-content'})
            if sections:
                for section in sections:
                    if 'mp-refs' in section['class']:
                        print('found ref')
                        continue
                    # Collect internal links
                    urls.extend(get_internal_links(section, url))
                    # Get the text data
                    text += section.get_text(separator=" ", strip=True)
            else:
                return

        # The term has a dedicated "Drugs, Herbs and Supplements" page
        elif "druginfo" in url or "genetics" in url:
            # Get the article element
            article = soup.find('article')
            if article:
                # Get all the description section elements
                sections = article.find_all('section')
                for section in sections:
                    # Collect internal links
                    urls.extend(get_internal_links(section, url))
                    # Get the text data
                    text += section.get_text(separator=" ", strip=True)

                # Get all the bottom section elements
                bottoms = article.findAll('div', {'class': "bottom"})
                for bottom in bottoms:
                    # Collect internal links
                    urls.extend(get_internal_links(bottom, url))
                    # Get the text data
                    text += bottom.get_text(separator=" ", strip=True)
            else:
                return

        # The term has a dedicated "Health Topics" page
        else:
            summary = soup.find(id="topic-summary")
            if summary:
                urls.extend(get_internal_links(summary, url))
                text += summary.get_text(separator=" ", strip=True)
            else:
                return

        side = soup.find('div', {'class': "side"})
        if side:
            urls.extend(get_internal_links(side, url))

        # Export into a text file
        if depth != DEPTH:
            output_file.write("\n\n")
        output_file.writelines(["[", url, "]\n"])
        output_file.write(text)

    # Crawl internal links
    for url in urls:
        get_document(output_file, url, depth-1, visited_urls)
    return

def main():
    # Build the search term string from commandline arguments 
    if len(sys.argv) > 1:
        terms = [" ".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])]
    else:
        terms = EXPERIMENTAL_TERMS

    # Instanciate the CSE handler
    search_obj = cse_handler.CSEHandler(API_KEY, CSE_ID)

    # Search for the given terms 
    for term in terms:
        # Search links
        links = search_obj.get_links_by_query(MEDLINE_URL, term)
        # print(links)

        # Try next term if no website was found
        if not len(links):
            print("Not Found")
            continue

        # Open the output file
        output_file_path = join(OUTPUT_DIR, term + ".txt")
        makedirs(dirname(output_file_path), exist_ok=True)
        output_file = open(output_file_path, 'w')

        # Extract documents
        #print(f'{term}:')
        get_document(output_file, links[0], DEPTH, [])

        # Close the output file
        output_file.close()

if __name__ == "__main__":
    main()