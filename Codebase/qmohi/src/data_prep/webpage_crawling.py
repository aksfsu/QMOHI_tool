"""
Get all the data from the URLs retrieved except document urls
Input - Relevant URLs (having presence of keywords)
Output - All the text content on those URLs
"""

from os.path import join
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd

'''
# Requirements for PDF/image support
import requests
from tempfile import TemporaryDirectory
import io
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def text_from_image(input_image):
    image = Image.open(input_image)
    text = str(pytesseract.image_to_string(image))
    return text

def get_text_in_images_from_html(html):
	soup = BeautifulSoup(html, 'html.parser')
	images = soup.find_all('img')
	texts = ""
	if len(images) > 0:
		for image in images:
			try:
				image_link = image["data-srcset"]
			except:
				try:
					image_link = image["data-src"]
				except:
					try:
						image_link = image["data-fallback-src"]
					except:
						try:
							image_link = image["src"]
						except:
							pass

			try:
				response = requests.get(image_link)   
				text = text_from_image(io.BytesIO(response.content))
				texts += " " + text
			except:
				pass
	
	return texts

def text_from_pdf(url):
	with TemporaryDirectory() as tempdir:
		# Converting PDF to images
		pdf_pages = convert_from_path(url, 500)
		image_file_list = []
		for i, page in enumerate(pdf_pages, start=1):
			filename = join(tempdir, f"page_{i}.jpg")
			page.save(filename, "JPEG")
			image_file_list.append(filename)

		# Recognizing text from the images using OCR
		print(f'Extracting text from PDF: {url} ...')
		texts = ""
		for image_file in image_file_list:
			text = str(pytesseract.image_to_string(Image.open(image_file)))
			text = text.replace("-\n", "")
			texts += " " + text
		return texts
'''

# Access web page content with Selenium
def html_from_selenium(url, driver_path):
	try:
		print("   - Issues in accessing URL content, trying with Selenium for ", url)
		options = Options()
		options.add_argument("--no-sandbox")
		options.add_argument("--headless")  # Runs Chrome in headless mode.
		options.add_argument('--disable-dev-shm-usage')

		# run web driver with the driver_path provided by user
		driver = webdriver.Chrome(driver_path, chrome_options=options)
		driver.get(url)
		html = driver.page_source
		return html

	except TimeoutException as e:
		print("Caught the TimeoutException with Selenium: ", e)
		return -1

	# If there is some error in URL redirection
	except Exception as e:
		print("Error in URL redirection!")
		print(e.msg)
		return -1

# Retrieving data from URL
def text_from_url(url, driver_path):
	try:
		# Normal user put restrictions on web scraping hence changed user agent
		headers = {'User-Agent': 'Mozilla/5.0'}
		request = Request(url, headers=headers)
		html = urlopen(request, timeout=100).read()

	# if problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		html = html_from_selenium(url, driver_path)
		if html == -1:
			return ""

	try:
		# Using html parser for retrieving text
		soup = BeautifulSoup(html, 'html.parser')

		# Kill all script and style elements
		for script in soup(["script", "style"]):
			script.extract()

		# Get text with beautiful soup
		text = soup.get_text()

		# Get text in images
		# text += " " + get_text_in_images_from_html(html) # Disabled for now

		return text

	# If problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		return ""

# Collect content from the given URLs
def retrieve_content_from_urls(input_dataframe, keywords, output_dir, driver_path):
	header = ['University name', 'University SHC URL', 'Count of SHC webpages matching keywords',
			  '', 'Content on all retrieved webpages', 'Total word count on all pages']
	output_dataframe = pd.DataFrame(columns=header)

	# For every university
	for index, row in input_dataframe.iterrows():
		complete_data = ""
		university = row['University name']
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']
		print("- ", university)

		# If links with keywords related content are present
		if len(link_data) != 0:
			visited_links = set()
			for data in link_data:
				link = data["url"]
				content_format = data["format"]
				if link not in visited_links:
					visited_links.add(link)
					if content_format == "pdf":
						pass
						'''
						# PDF/image support disabled for now
						text = text_from_pdf(link)
						if text:
							complete_data = complete_data + " " + text
						'''
					else:
						text = text_from_url(link, driver_path)
						if text:
							complete_data = complete_data + " " + text

			complete_data = re.sub(r'\n\s*\n', '\n', complete_data)

			# Calculating total number of words on all web pages
			total_words = len(complete_data.split())

			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of SHC webpages matching keywords': no_of_links,
														'Keywords matched webpages on SHC': link_data,
														'Content on all retrieved webpages': complete_data,
														'Total word count on all pages': total_words,
														}, ignore_index=True)
	# Storing result
	output_dataframe.to_csv(output_dir + '/get_data_from_url_output_links.csv')

	return output_dataframe
