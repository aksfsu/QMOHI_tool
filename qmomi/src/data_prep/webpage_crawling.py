'''
Get all the data from the URLs retrieved except pdf and document urls
Input - Relevant URLs (having presence of keywords)
Output - All the text content on those URLs
'''

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd
from bs4.element import Comment
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.common import exceptions
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from nltk.tokenize import word_tokenize
import requests


class URL_content:

	def __init__(self, url):
		self.url = url

def tag_visible(element):
	if element.parent.name in ['style', 'script']: #, 'head', 'title', 'meta', '[document]']:
		return False
	if isinstance(element, Comment):
		return False
	return True

def html_from_selenium(url_obj, driver_path):

	try:
		print("Issues in accessing URL content by Request, trying with Selenium: ")
		options = Options()
		options.add_argument("--headless")  # Runs Chrome in headless mode.

		# run web driver with the driver_path provided by user
		driver = webdriver.Chrome(driver_path, chrome_options=options)
		# driver = webdriver.Chrome(executable_path=r"/Users/tejasvibelsare/Downloads/chromedriver")
		driver.get(url_obj.url)
		html = driver.page_source
		return html

	except TimeoutException as e:
		print("Caught the TimeoutException with Selenium: ", e)
		return -1

	except exceptions as e:  ### if there is some error in URL redirection
		print("Error in URL redirection!")
		print(e.msg)
		return -1

## retrieving data from URL
def data_from_url(url_obj, driver_path):

	# try:
	# 	driver = webdriver.Chrome(executable_path=r"/Users/tejasvibelsare/Downloads/chromedriver")
	# 	driver.get(self.url)
	# 	html = driver.page_source
	# 	soup = BeautifulSoup(html, 'html.parser')  # Parse html code
	#
	# 	texts = soup.findAll(text=True)  # find all text
	#
	# 	visible_texts = filter(self.tag_visible, texts)
	# 	text = u"\n".join(t.strip() for t in visible_texts)
	# 	return text
	try:

		##changed user agent as with normal user, it was putting restrictions on web scraping
		headers = {'User-Agent': 'Mozilla/5.0'}
		request = Request(url_obj.url, headers=headers)
		html = urlopen(request, timeout=100).read()

	except Exception as e:  ##if problem in accessing URL
		print("Exception : ", e)
		html = html_from_selenium(url_obj, driver_path)

		if html == -1:
			return " "
	try:
		soup = BeautifulSoup(html, 'html.parser')  ##using html parser for retrieving text

		# kill all script and style elements
		for script in soup(["script", "style"]):
			script.extract()

		# get text with beautiful soup
		text = soup.get_text()
		return text

	except Exception as e:  ##if problem in accessing URL
		print("Exception : ", e)
		return " "

		# page = requests.get(self.url)  # to extract page from website
		# html_code = page.content  # to extract html code from page
		#
		# soup = BeautifulSoup(html_code, 'html.parser')  # Parse html code
		#
		# texts = soup.findAll(text=True)  # find all text
		#
		# text_from_html = ' '.join(texts)  # join all text
		# text_extracted = text_from_html.encode("utf-8")
		# text_extracted = str(text_extracted)
		# words_tokenized = word_tokenize(text_extracted)
		# return words_tokenized



	# except Exception as e:  ##if problem in accessing URL
	# 	print("Issues in accessing URL content : ", e)
	# 	return " "




##### remove tags and unwanted data here
def remove_unwanted_data(complete_data, keywords):
	complete_data_series = pd.Series(complete_data.split("\n"))

	for index, row in complete_data_series.iteritems():
		# access data using column names

		if (len(row.split()) < 4) and (all(
				x not in row for x in keywords)):  # keywords not in row and length of row is less than 4
			complete_data_series.drop(labels=[index], inplace=True)

	content_after_removing_unwanted_data = '\n'.join(complete_data_series)  ## join final data with new line character

	return content_after_removing_unwanted_data


### Collect content from the given URLs
def retrieve_content_from_urls(input_dataframe, keywords, output_dir, driver_path):
	header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC',
			  'Keywords matched webpages on SHC',
			  'Content on all retrieved webpages', 'Total word count on all pages']
	output_dataframe = pd.DataFrame(columns=header)

	##for every university
	for index, row in input_dataframe.iterrows():

		complete_data = ""

		university = row['University name']
		shc = row['University SHC URL']
		no_of_links = row['Count of keywords matching webpages on SHC']
		links = row['Keywords matched webpages on SHC']

		# ####### change these 2 lines only when you are reading from csv and not passing dataframe from previous python file
		# if links != '[]':  ### if links with LARC related content are present
		#
		#     links = re.findall(r"'(.*?)'", links)  ##### convert string into list
		if isinstance(links, str):
			links = re.findall(r"'(.*?)'", links)
		# #### for every link in links
		if len(links) != 0:  ### if links with keywords related content are present

			#  remove duplicate sentences from data
			seen = set()
			unique_links = []
			for link in links:
				if link not in seen:
					seen.add(link)
					unique_links.append(link)

			for each_link in unique_links:

				url_obj = URL_content(each_link)

				print(each_link)

				# splitted_url = each_link.rsplit('/', 1)
				#
				# print("Splitted url {}",splitted_url)

				if each_link.endswith(".pdf"): #or ".pdf" in splitted_url[1]:

					# url_content = url_obj.get_txt_from_pdf()
					# print(url_content)
					print("PDF!")
					url_content = ""

				elif each_link.endswith(".docx") or each_link.endswith(".doc"):
					print("DOCS!")
					url_content = ""

				else:
					url_content = data_from_url(url_obj, driver_path)

				complete_data = complete_data + " " + str(url_content)

			complete_data = re.sub(r'\n\s*\n', '\n\n', complete_data)
			# complete_data = complete_data.replace('\n', 'weird_char')

			### calculating total number of words on all webpages
			total_words = complete_data
			total_words = len(total_words.split())

			content_after_removing_unwanted_data = remove_unwanted_data(complete_data, keywords)
			final_content = content_after_removing_unwanted_data.replace('\n', '. \n')

			# final_content = complete_data.replace('\n', '. \n')
			final_content = final_content.replace('..', '. ')

			'''
			## make separate text file for every university with content from all the links
			text_file_content = "data/content_from_links_without_pdf/"+ university + ".txt"
			f = open(text_file_content, "w+")
			f.write(final_content)
			'''

			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of keywords matching webpages on SHC': no_of_links,
														'Keywords matched webpages on SHC': links,
														'Content on all retrieved webpages': final_content,
														'Total word count on all pages': total_words,
														}, ignore_index=True)

	output_dataframe.to_csv(output_dir + '/get_data_from_url_output_without_pdf_links.csv')  ## storing result

	return output_dataframe

# input_dataframe = pd.read_csv('/Users/tejasvibelsare/Desktop/larc/Output 2020-07-08 11:48:19/keywords_matched_webpages_on_SHC.csv')
# keywords = ['IUD','Progesterone IUD','Progestin','Hormonal IUD','Mirena','Skyla','Kyleena','Liletta','Copper IUD',
# 			'Non-Hormonal IUD','nonhormonal iud','Paragard','contraceptive implant','Nexplanon',
# 			'contraceptive injection','control shot','Depo-Provera','Depo']
#
# output_dir = "/Users/tejasvibelsare/Desktop/larc/Output 2020-07-08 11:48:19/"
# driver_path = "/Users/tejasvibelsare/Downloads/chromedriver"
#
# retrieve_content_from_urls(input_dataframe, keywords, output_dir, driver_path)
