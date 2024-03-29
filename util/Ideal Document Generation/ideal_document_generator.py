from bs4 import BeautifulSoup
from os.path import join, dirname
from os import makedirs
import sys
import re

import config 
import cse_handler

import asyncio
import pyppeteer

from drugbank_db_handler import DrugBankDBHandler

# Config constants
API_KEY = config.MY_API_KEY
CSE_ID = config.MY_CSE_ID
MEDLINE_URL = "https://medlineplus.gov"
MEDLINE_DRUGINFO_URL = "https://medlineplus.gov/druginfo"
DRUGBANK_URL = "https://go.drugbank.com/drugs/"
DEPTH = 2 # (>= 1)
THERAPY_NUM = 5
OUTPUT_DIR = "./output"

# Experimental terms
EXPERIMENTAL_TERMS = [
    [
        "Contraception",
        # "Contraceptive", 
        # "Levonorgestrel", 
        # "Progestin", 
        # "Progesterone", 
        # "IUD", 
        # "Mifepristone", 
        # "Implant",
    ],
    [
        "LARC",
        # "Progesterone",
        # "Hormonal IUD",
        # "Copper IUD",
        # "Paragard",
        # "Nexplanon",
        # "Depo-Provera"
    ],
    ["Accidental Injury"],
    ["Broken Limbs"],
    ["First Aid"],
    ["Allergy"],
    ["Asthma"],
    ["Flu"],
    ["Cold"],
    ["Standard Immunizations"],
    ["Vaccines"],
    ["Tobacco"],
    ["Alcohol"],
    ["Drug Issues"],
    ["Mental Health Depression"],
    ["Anxiety"],
    ["Stress"],
    ["Time Management"],
    ["Abortion"],
    ["Medicated Abortion"],
    ["Sexual Harrassment"],
    ["Abuse"],
    ["Assault"],
    ["Violence"],
    ["Body Image"],
    ["Nutrition"],
    ["Obesity"],
    ["HIV"],
    ["STD"],
    ["Sexual Health"],
    ["Safe Sex"],
    ["Urinary Tract Infections"],
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
        return visited_urls

    # Get the HTML based on URL
    html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve information only once from the same websites
    urls = []
    if url not in visited_urls:
        visited_urls.add(url)

        text = ""
        # The term has a dedicated "Medical Encyclopedia" page
        if "ency" in url:
            # Get the summary element
            summary = soup.find(id="ency_summary")
            if summary:
                # Collect internal links
                urls.extend(get_internal_links(summary, url))
                # Get the text data
                text += summary.get_text(separator=" ", strip=True) + " "
                # Get all the sections
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
                        text += section_body.get_text(separator=" ", strip=True) + " "
            else:
                return visited_urls 

        # The term has a dedicated "Lab Tests" page
        elif "lab-tests" in url:
            # Get the main description element
            sections = soup.find_all('div', {'class': 'mp-content'})
            if sections:
                for section in sections:
                    if 'mp-refs' in section['class']:
                        continue
                    # Collect internal links
                    urls.extend(get_internal_links(section, url))
                    # Get the text data
                    text += section.get_text(separator=" ", strip=True) + " "
            else:
                return visited_urls

        # The term has a dedicated "Drugs, Herbs and Supplements" page
        elif "druginfo" in url:
            # Get all the sections
            sections = soup.find_all('div', {'class': 'section'})
            if sections:
                for section in sections:
                    section_body = section.find('div', {'id': re.compile('section-1')})
                    if section_body:
                        # Collect internal links
                        urls.extend(get_internal_links(section_body, url))
                        # Get the text data
                        text += section_body.get_text(separator=" ", strip=True) + " "
                    
                    section_brandname = section.find('div', {'id': re.compile(r'section-brandname-\d+')})
                    if section_brandname:
                        # Collect internal links
                        urls.extend(get_internal_links(section_brandname, url))
                        # Get the text data
                        text += section_brandname.get_text(separator=" ", strip=True) + " "

                    section_other_name = section.find('div', {'id': re.compile('section-other-name')})
                    if section_other_name:
                        # Collect internal links
                        urls.extend(get_internal_links(section_other_name, url))
                        # Get the text data
                        text += section_other_name.get_text(separator=" ", strip=True) + " "
            else:
                return visited_urls

        # The term has a dedicated "Health Topics" page
        else:
            summary = soup.find(id="topic-summary")
            if summary:
                urls.extend(get_internal_links(summary, url))
                text += summary.get_text(separator=" ", strip=True)
            else:
                return visited_urls

        side = soup.find('div', {'class': "side"})
        if side:
            urls.extend(get_internal_links(side, url))

        # Export into a text file
        output_file.writelines(["[", url, "]\n"])
        output_file.write(text)
        output_file.write("\n\n")

    # Crawl internal links
    for url in urls:
        get_document(output_file, url, depth-1, visited_urls)
    return visited_urls


def get_drugbank_information(output_file, url):
    # Get the HTML based on URL
    try:
        html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    except:
        return

    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    text = ""

    # Get the summary
    summary = soup.find('dt', {'id': 'summary'})
    if summary:
        summary = summary.find_next_sibling()
        if summary:
            # Get the text data
            text += summary.get_text(separator=" ", strip=True) + " "

    # Get the brand names
    brand_names = soup.find('dt', {'id': 'brand-names'})
    if brand_names:
        brand_names = brand_names.find_next_sibling()
        if brand_names:
            # Get the text data
            text += brand_names.get_text(separator=" ", strip=True) + " "

    # Get the brand names
    background = soup.find('dt', {'id': 'background'})
    if background:
        background = background.find_next_sibling()
        if background:
            # Get the text data
            text += background.get_text(separator=" ", strip=True) + " "

    # Get the brand names
    indication = soup.find('dt', {'id': 'indication'})
    if indication:
        indication = indication.find_next_sibling()
        if indication:
            indication_ps = indication.find_all('p')
            for p in indication_ps:
                # Get the text data
                text += p.get_text(separator=" ", strip=True) + " "

    output_file.write("\n\n")
    output_file.writelines(["[", url, "]\n"])
    output_file.write(text)


def generate_ideal_document(output_file_path, keywords=[], drug_names=[]):
    # Instanciate the CSE handler
    search_obj = cse_handler.CSEHandler(API_KEY, CSE_ID)

    ### Method 3: DrugBank Information with DrugBank Data in XML
    # drugbank = DrugBankDBHandler()

    # Open the output file
    makedirs(dirname(output_file_path), exist_ok=True)
    output_file = open(output_file_path, 'w')

    visited_urls = set()

    for keyword in keywords:
        links = search_obj.get_links_by_query(MEDLINE_URL, keyword)
        # print(links)

        # Try next term if no website was found
        if not len(links):
            print("Not Found")
            return

        # Extract documents
        #print(f'{topics}:')
        visited_urls.update(get_document(output_file, links[0], depth=DEPTH, visited_urls=visited_urls))

    # Collect therapy information
    ### Method 1: MedlinePlus Drug, Herbs and Suppliments database
    # therapy_links = search_obj.get_links_by_query(MEDLINE_DRUGINFO_URL, topics)
    # for link in therapy_links[:min(len(therapy_links), THERAPY_NUM)]:
    #     visited_urls.update(get_document(output_file, link, depth=1, visited_urls=visited_urls))

    ### Method 2: DrugBank Information with Google API
    #### Method 2-1: Use topics and keywords
    for keyword in keywords:
        therapy_links = search_obj.get_links_by_query(DRUGBANK_URL, '"summary" ' + keyword)
        for link in therapy_links[:min(len(therapy_links), THERAPY_NUM)]:
            if link not in visited_urls:
                visited_urls.add(link)
                get_drugbank_information(output_file, link)

    #### Method 2-2: Use drug names
    for drug_name in drug_names:
        therapy_links = search_obj.get_links_by_query(DRUGBANK_URL, '"summary" ' + drug_name)
        link = therapy_links[0]
        if link not in visited_urls:
            visited_urls.add(link)
            get_drugbank_information(output_file, link)

    ### Method 3: DrugBank Information with DrugBank Data in XML
    # drugbank.search_drugbank(keywords, drug_names)
    # drugbank.write_to_opened_file(output_file)

    # Close the output file
    output_file.close()



# Input: A list of keywords where the first item is the topic
def main():
    # Build the search term string from commandline arguments 
    if len(sys.argv) > 1:
        terms = sys.argv[1:]
        output_file_path = join(OUTPUT_DIR, terms[0] + ".txt")
        generate_ideal_document(output_file_path, terms)
    else:
        for terms in EXPERIMENTAL_TERMS:
            output_file_path = join(OUTPUT_DIR, terms[0] + ".txt")
            generate_ideal_document(output_file_path, terms)


if __name__ == "__main__":
    main()
