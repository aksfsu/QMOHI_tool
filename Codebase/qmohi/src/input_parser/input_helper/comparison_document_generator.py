from bs4 import BeautifulSoup
from os.path import dirname
from os import makedirs
import re
from nltk.stem import WordNetLemmatizer

from qmohi.src.input_parser.input_helper.cse_handler import CSEHandler

import asyncio
import pyppeteer

# Config constants
MEDLINEPLUS_URL = "https://medlineplus.gov"
MEDLINEPLUS_DRUGS_URL = "https://medlineplus.gov/druginfo/meds/"
DRUGBANK_URL = "https://go.drugbank.com/drugs/"


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
def get_internal_links(soup, parent_url):
    internal_links = []
    for a in soup.findAll('a', href=True):
        link = a['href']
        if not link:
            print("No URL assigned")
        elif MEDLINEPLUS_URL in link:
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


def clean_drug_name(drug):
    drug = drug.replace("®", "").replace("¶", "")
    drug = re.sub(r"\(.*\)", "", drug)
    drug = re.sub(r"[\",#/@;:<>{}`_+=~|\[\]]", " ", drug)
    drug = drug.strip().lower()
    if not re.search(r".*\..*", drug):
        drug = re.sub(r"([a-z]+)-(\d+)", r"\1\2", drug)
        drug = re.sub(r"(\d+)-([a-z]+)", r"\1\2", drug)
        drug = re.sub(r"([a-zA-Z]+) (\d+)$", r"\1\2", drug)
        drug = re.sub(r"^(\d+) ([a-z]+)", r"\1\2", drug)
    drug = re.sub(r"-", " ", drug)
    drug = re.sub(r" +", " ", drug)
    return drug


def lemmatize_word(word):
    lemmatizer = WordNetLemmatizer()
    return " ".join([lemmatizer.lemmatize(w) for w in word])


# Get text data and export in the output file
def get_comparison_document(output_file, url, depth, visited_urls, drug_keywords, drug_details):
    if depth == 0:
        return

    # Get the HTML based on URL
    html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve information only once from the same websites
    urls = []
    if url not in visited_urls:
        visited_urls.add(url)
        text = ""
        drugs = []

        # The term has a dedicated "Medical Encyclopedia" page
        if "ency" in url:
            # Get the page title element
            title = soup.find(class_="page-title")
            if title:
                # Get the text data
                text += title.get_text(separator=" ", strip=True) + " "

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
                return
            if sections:
                for section in sections:
                    section_body = section.find('div', {'id': re.compile(r'section-\d+')})
                    if section_body:
                        # Collect internal links
                        urls.extend(get_internal_links(section_body, url))
                        # Get the text data
                        text += section_body.get_text(separator=" ", strip=True) + " "
            else:
                return 

        # The term has a dedicated "Lab Tests" page
        elif "lab-tests" in url:
            # Get the page title element
            title = soup.find(class_="page-title")
            if title:
                # Get the text data
                text += title.get_text(separator=" ", strip=True) + " "

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
                return

        # The term has a dedicated "Drugs, Herbs and Supplements" page
        elif "druginfo" in url and re.search(r"\d+\.html$", url):
            drug_text = ""

            h1 = soup.find('h1')
            if h1:
                h1 = h1.get_text(separator=" ", strip=True)
                h1 = clean_drug_name(h1)
                drugs.append(h1)
                drug_text += h1 + " "

            # Get all the sections
            sections = soup.find_all('div', {'class': 'section'})
            if sections:
                for section in sections:
                    # Extract descriptions of the drug
                    section_body = section.find('div', {'id': re.compile(r'section-\d+')})
                    if section_body:
                        # Collect internal links
                        urls.extend(get_internal_links(section_body, url))
                        # Get the text data
                        drug_text += section_body.parent.get_text(separator=" ", strip=True) + " "

                    # Extract drug names
                    section_brandname = section.find('div', {'id': re.compile(r'section-brandname')})
                    if section_brandname:
                        # Collect internal links
                        urls.extend(get_internal_links(section_brandname, url))
                        # Extract drug names
                        list_items = section_brandname.find_all('li')
                        for item in list_items:
                            item_text = item.get_text(separator=" ", strip=True)
                            item_text = clean_drug_name(item_text)
                            drugs.append(item_text)
                            drug_text += item_text + " "

                    section_other_name = section.find('div', {'id': re.compile('section-other-name')})
                    if section_other_name:
                        # Collect internal links
                        urls.extend(get_internal_links(section_other_name, url))
                        # Extract drug names
                        list_items = section_other_name.find_all('li')
                        for item in list_items:
                            item_text = item.get_text(separator=" ", strip=True)
                            item_text = clean_drug_name(item_text)
                            drugs.append(item_text)
                            drug_text += item_text + " "

                if drug_details:
                    text += drug_text + " "
            else:
                return

        # The term has a dedicated "Health Topics" page
        else:
            # Get the page title element
            title = soup.find(class_="page-title")
            if title:
                # Get the text data
                text += title.get_text(separator=" ", strip=True) + " "

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
        if text:
            output_file.writelines(["[", url, "]\n"])
            output_file.write(text)
            output_file.write("\n\n")

        for drug in drugs:
            if not drug in drug_keywords:
                drug_keywords.append(drug)

    # Crawl internal links
    for url in urls:
        get_comparison_document(output_file, url, depth-1, visited_urls, drug_keywords, drug_details)
    return


def get_drugbank_information(output_file, url, drug_keywords, drug_details):
    # Get the HTML based on URL
    try:
        html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    except:
        return

    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    text = ""
    drugs = []

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
            brand_names = brand_names.get_text(separator=" ", strip=True)
            brand_names = brand_names.split(", ")
            for brand_name in brand_names:
                brand_name = clean_drug_name(brand_name)
                drugs.append(brand_name)
                text += brand_name + " "

    # Get the generic name
    generic_names = soup.find('dt', {'id': 'generic-name'})
    if generic_names:
        generic_names = generic_names.find_next_sibling()
        if generic_names:
            # Get the text data
            generic_names = generic_names.get_text(separator=",", strip=True).replace("(", "").replace(")", "")
            generic_names = generic_names.split(", ")
            for generic_name in generic_names:
                generic_name = clean_drug_name(generic_name)
                drugs.append(generic_name)
                text += generic_name + " "
            
    # Get the external IDs
    extids_names = soup.find('dt', {'id': 'external-ids'})
    if extids_names:
        extids_names = extids_names.find_next_sibling()
        if extids_names:
            extids_names = extids_names.find_all('li')
            for extids_name in extids_names:
                # Get the text data
                extids_name = extids_name.get_text(separator=" ", strip=True).replace("(", "").replace(")", "")
                extids_name = clean_drug_name(extids_name)
                drugs.append(extids_name)
                text += extids_name + " "

    # Get the background
    background = soup.find('dt', {'id': 'background'})
    if background:
        background = background.find_next_sibling()
        if background:
            # Get the text data
            background = background.get_text(separator=" ", strip=True)

    # Get the indication
    indication = soup.find('dt', {'id': 'indication'})
    if indication:
        indication = indication.find_next_sibling()
        if indication:
            indication_ps = indication.find_all('p')
            for p in indication_ps:
                # Get the text data
                text += p.get_text(separator=" ", strip=True) + " "

    if drug_details and text:
        output_file.write("\n\n")
        output_file.writelines(["[", url, "]\n"])
        output_file.write(text)

    for drug in drugs:
        if not drug in drug_keywords:
            drug_keywords.append(drug)


def sort_drugs(drugs, keywords):
    relevant_drugs = [[] for i in range(len(keywords))]
    other_drugs = []
    for drug in drugs:
        for i, keyword in enumerate(keywords):
            if keyword in drug or drug in keyword:
                relevant_drugs[i].append(drug)
        else:
            other_drugs.append(drug)
    return [drug for relevant_drug in relevant_drugs for drug in relevant_drug] + other_drugs


def generate_comparison_document(output_file_path, api_keys, cse_id, depth, num_of_therapy=5, keywords=[], drug_details=True):
    # Instanciate the CSE handler
    search_obj = CSEHandler(api_keys[0], cse_id)

    # Open the output file
    makedirs(dirname(output_file_path), exist_ok=True)
    output_file = open(output_file_path, 'w')

    visited_urls = set()
    drug_keywords = []

    for i, keyword in enumerate(keywords):
        print(f"   Search Term: {keyword}")
        links = search_obj.get_links_by_query(MEDLINEPLUS_URL, keyword)
        links = [link["url"] for link in links]
        # print(links)

        # Try next term if no website was found
        if not len(links):
            continue

        # Extract documents
        print("   Collecting gerenal description...")
        get_comparison_document(output_file, links[0], 2 if i == 0 else depth, visited_urls, drug_keywords, drug_details)

        print("   Collecting therapy information...")

        # DrugBank Information on MedlinePlus Drug DB
        query = '"' + keyword + '"'
        lemmatized_keyword = lemmatize_word(keyword)
        if lemmatized_keyword != keyword:
            query += ' OR "' + lemmatized_keyword + '"'
        links = search_obj.get_links_by_query(MEDLINEPLUS_DRUGS_URL, query)
        links = [link["url"] for link in links]
        # print(links)
        for link in links:
            if link not in visited_urls:
                get_comparison_document(output_file, link, 1, visited_urls, drug_keywords, drug_details)

        # DrugBank Information on DrugBank
        therapy_links = search_obj.get_links_by_query(DRUGBANK_URL, query)
        therapy_links = [link["url"] for link in therapy_links]
        for link in therapy_links[:min(len(therapy_links), num_of_therapy)]:
            link = re.sub(r"(DB\d+)/.*", r"\1", link)
            if link not in visited_urls:
                visited_urls.add(link)
                get_drugbank_information(output_file, link, drug_keywords, drug_details)

    # Close the output file
    output_file.close()

    drug_keywords = sort_drugs(drug_keywords, keywords)
    return drug_keywords
