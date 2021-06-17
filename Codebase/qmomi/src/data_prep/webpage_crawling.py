"""
Get all the data from the URLs retrieved except pdf and document urls
Input - Relevant URLs (having presence of keywords)
Output - All the text content on those URLs
"""

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from bs4.element import Comment
import re
import pandas as pd
import time
import datetime


class UrlContent:

	def __init__(self, url):
		self.url = url


# Remove styling tags
def tag_visible(element):
	if element.parent.name in ['style', 'script']:
		return False
	if isinstance(element, Comment):
		return False
	return True


# Access web page content with Selenium
def html_from_selenium(url_obj, driver_path):
	try:
		print("   - Issues in accessing URL content, trying with Selenium for ", url_obj.url)
		options = Options()
		options.add_argument("--no-sandbox")
		options.add_argument("--headless")  # Runs Chrome in headless mode.
		options.add_argument('--disable-dev-shm-usage')
		
		# run web driver with the driver_path provided by user
		driver = webdriver.Chrome(driver_path, chrome_options=options)
		# driver = webdriver.Chrome(executable_path=r"/Users/tejasvibelsare/Downloads/chromedriver")
		driver.get(url_obj.url)
		html = driver.page_source
		return html

	except TimeoutException as e:
		print("Caught the TimeoutException with Selenium: ", e)
		return -1

	# If there is some error in URL redirection
	except exceptions as e:
		print("Error in URL redirection!")
		print(e.msg)
		return -1


# Retrieving data from URL
def data_from_url(url_obj, driver_path):
	try:
		# Normal user put restrictions on web scraping hence changed user agent
		headers = {'User-Agent': 'Mozilla/5.0'}
		request = Request(url_obj.url, headers=headers)
		html = urlopen(request, timeout=100).read()

	# if problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		html = html_from_selenium(url_obj, driver_path)

		if html == -1:
			return " "
	try:
		# Using html parser for retrieving text
		soup = BeautifulSoup(html, 'html.parser')

		# Kill all script and style elements
		for script in soup(["script", "style"]):
			script.extract()

		# Get text with beautiful soup
		text = soup.get_text()
		return text

	# If problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		return " "


# Remove tags and unwanted data here
def remove_unwanted_data(complete_data, keywords):
	complete_data_series = pd.Series(complete_data.split("\n"))

	for index, row in complete_data_series.iteritems():

		# Keywords not in row and length of row is less than 4
		if (len(row.split()) < 4) and (all(x not in row for x in keywords)):
			complete_data_series.drop(labels=[index], inplace=True)

	# Join final data with new line character
	content_after_removing_unwanted_data = '\n'.join(complete_data_series)

	return content_after_removing_unwanted_data


# Collect content from the given URLs
def retrieve_content_from_urls(input_dataframe, keywords, output_dir, driver_path):
	header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC',
			  'Keywords matched webpages on SHC', 'Content on all retrieved webpages', 'Total word count on all pages']
	output_dataframe = pd.DataFrame(columns=header)

	# For every university
	for index, row in input_dataframe.iterrows():
		timestamp = time.time()
		date = datetime.datetime.fromtimestamp(timestamp)
		print("Start:", date.strftime('%H:%M:%S.%f'))

		complete_data = ""
		university = row['University name']
		shc = row['University SHC URL']
		no_of_links = row['Count of keywords matching webpages on SHC']
		links = row['Keywords matched webpages on SHC']
		print("- ", university)

		if isinstance(links, str):
			links = re.findall(r"'(.*?)'", links)

		# If links with keywords related content are present
		if len(links) != 0:

			#  Remove duplicate sentences from data
			seen = set()
			unique_links = []
			for link in links:
				if link not in seen:
					seen.add(link)
					unique_links.append(link)

			for each_link in unique_links:
				url_obj = UrlContent(each_link)

				if each_link.endswith(".pdf"):
					url_content = ""

				elif each_link.endswith(".docx") or each_link.endswith(".doc"):
					url_content = ""

				else:
					url_content = data_from_url(url_obj, driver_path)

				complete_data = complete_data + " " + str(url_content)

			complete_data = re.sub(r'\n\s*\n', '\n\n', complete_data)

			# Calculating total number of words on all web pages
			total_words = complete_data
			total_words = len(total_words.split())

			content_after_removing_unwanted_data = remove_unwanted_data(complete_data, keywords)
			final_content = content_after_removing_unwanted_data.replace('\n', '. \n')
			final_content = final_content.replace('..', '. ')

			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of keywords matching webpages on SHC': no_of_links,
														'Keywords matched webpages on SHC': links,
														'Content on all retrieved webpages': final_content,
														'Total word count on all pages': total_words,
														}, ignore_index=True)
		timestamp = time.time()
		date = datetime.datetime.fromtimestamp(timestamp)
		print("End:", date.strftime('%H:%M:%S.%f'))
	# Storing result
	output_dataframe.to_csv(output_dir + '/get_data_from_url_output_without_pdf_links.csv')

	return output_dataframe
