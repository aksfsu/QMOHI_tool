import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from os.path import join, dirname
from os import makedirs
import sys
import re

import asyncio
import pyppeteer

MEDLINE_URL = "https://medlineplus.gov"
DEPTH = 2 # >= 1
OUTPUT_DIR = "./output"

# Experimental terms
EXPERIMENTAL_TERMS = [
    "Accidental%20Injury", #
    "Broken%20Limbs",
    "First%20Aid", #
    "Allergy", #
    "Asthma",
    "Flu",
    "Cold", #
    "Standard%20Immunizations",
    "Vaccines", #
    "Tobacco",
    "Alcohol",
    "Drug%20Issues",
    "Mental%20Health%20Depression",
    "Anxiety",
    "Stress",
    "Time%20Management",
    "Abortion",
    "Medicated%20Abortion",
    "Sexual%20Harrassment",
    "Abuse",
    "Assault",
    "Violence",
    "Body%20Image",
    "Nutrition",
    "Obesity",
    "HIV",
    "STD",
    "Sexual%20Health",
    "Safe%20Sex",
    "Urinary%20Tract%20Infections",
]

# Use MedlinePlus Web Service API with the term
async def exec_medlineplus_web_service(term):
    browser = await pyppeteer.launch({
        'args': ['--no-sandbox', '--disable-dev-shm-usage']
    })
    page = await browser.newPage()
    await page.goto("https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term="+term)
    xml = await page.content()
    await browser.close()
    return xml

# Get URLs MedlinePlus API returns
def get_urls_from_query(term):
	# Get the XML 
	xml = asyncio.get_event_loop().run_until_complete(exec_medlineplus_web_service(term))
	# Pass the XML to the XML parset
	tree = ET.fromstring(xml)
	# Identify the summary of the term
	return [d.attrib['url'] for d in tree.iter('document')]

# Get all the text in all the hit URLs
def write_documents_from_query(output_file, term):
	# Get the XML 
	xml = asyncio.get_event_loop().run_until_complete(exec_medlineplus_web_service(term))
	# Pass the XML to the XML parset
	tree = ET.fromstring(xml)
	# Identify the summary of the term
	documents = [d for d in tree.iter('document')]
	for document in documents:
		document_attrib_dict = document.attrib
		if document_attrib_dict:
			url = document_attrib_dict['url']

		for content in document.findall('content'):
			if content.get('name') == "FullSummary":
				# Remove xml tags from the text
				bs_summary = BeautifulSoup(content.text, "html.parser")
				summary = bs_summary.get_text(separator=" ", strip=True)
				#print(f'summary: {summary}')
				break

		# Export into a text file
		if url:
			output_file.writelines(['Source: ', url, "\n"])
		if summary:
			output_file.writelines([summary, "\n\n"])
	return

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
	for a in soup.find_all('a', href=True):
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
def write_document(output_file, url, depth, visited_urls):
	if depth == 0:
		return visited_urls

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
				sections = summary.parent.find_all(class_="section")
			else:
				return visited_urls
			if sections:
				for section in sections:
					section_body = section.find(class_="section-body")
					if section_body:
						# Collect internal links
						urls.extend(get_internal_links(section_body, url))
						# Get the text data
						text += section_body.get_text(separator=" ", strip=True)

		# The term has a dedicated "Lab Tests" page
		elif "lab-tests" in url:
			# Get the main description element
			description = soup.find('div', {'class': "main"})
			if description:
				# Collect internal links
				urls.extend(get_internal_links(description, url))
				# Get the text data
				text += description.get_text(separator=" ", strip=True)
			else:
				return visited_urls

		# The term has a dedicated "Drugs, Herbs and Supplements" page
		elif "druginfo" in url or "genetics" in url:
			# Get the article element
			article = soup.find('article')
			if article:
				# Get all the description section elements
				descriptions = article.find_all('section')
				for description in descriptions:
					# Collect internal links
					urls.extend(get_internal_links(description, url))
					# Get the text data
					text += description.get_text(separator=" ", strip=True)

				# Get all the bottom section elements
				bottoms = article.find_all('div', {'class': "bottom"})
				for bottom in bottoms:
					# Collect internal links
					urls.extend(get_internal_links(bottom, url))
					# Get the text data
					text += bottom.get_text(separator=" ", strip=True)
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
		if depth != DEPTH:
			output_file.write("\n\n")
		output_file.writelines(['Source: ', url, "\n", text])

	# Crawl internal links
	for url in urls:
		write_document(output_file, url, depth-1, visited_urls)
	return visited_urls

def main():
	if len(sys.argv) > 1:
		# Build the search term string from commandline arguments 
		terms = ["%20".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])]
	else:
		terms = EXPERIMENTAL_TERMS

	# Search for the given terms 
	for term in terms:
		# Get the url for the term
		urls = get_urls_from_query(term)
		# print(urls)
        # Try next term if no website was found
		if not urls:
			print("Not Found")
			continue

		# Open the output file
		output_file_path = join(OUTPUT_DIR, term.replace("%20", " ") + ".txt")
		makedirs(dirname(output_file_path), exist_ok=True)
		output_file = open(output_file_path, 'w')

		# Extract documents
		# print(f'{term.replace("%20", " ")}:')
		### Method 1. Use all the URLs MedlinePlus API returns and crawl internal links
		# visited_urls = []
		# for url in urls:
		# 	visited_urls = write_document(output_file, url, DEPTH, visited_urls)
		### Method 2. Use the first hit only and crawl internal links
		write_document(output_file, urls[0], DEPTH, [])
		### Method 3. Use all the URLs MedlinePlus API returns
		# write_documents_from_query(output_file, term)

		# Close the output file
		output_file.close()

if __name__ == "__main__":
    main()