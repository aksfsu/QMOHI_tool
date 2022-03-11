"""
Get university SHC from university name
Input - list of university names
Output - list of university SHCs
"""

from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from selenium.common.exceptions import WebDriverException
import pandas as pd
import numpy as np
import re
import sys


# Building Google custom search engine
def google_search(search_term, api_key, cse_id, **kwargs):
	try:
		service = build("customsearch", "v1", developerKey=api_key)
		res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
		if('items' in res):
			return res['items']

	except Exception as e:
		print("Error in google search : ", e)
		sys.exit()


# Get redirected URL with the help of headless browser and chrome driver
def get_redirected_url(url, driver_path):
	options = Options()
	options.add_argument("--headless")  # Runs Chrome in headless mode.

	# Run web driver with the driver_path provided by user
	driver = webdriver.Chrome(driver_path, chrome_options=options)

	# Try getting redirected URL
	try:
		driver.get(url)
		redirected_url = driver.current_url
		return redirected_url

	except WebDriverException as e:
		print("Web driver exception in selenium :", e.msg)

	# If there is some error in URL redirection
	except exceptions as e:
		print("Error in URL redirection!")
		print(e.msg)

	return url


# Removing sub-urls from the program retrieved URLs
def remove_sub_urls(url):
	# Remove / in the end if it exist
	if url.endswith('/'):
		removed_slash = url.rsplit('/', 1)
		url = removed_slash[0]

	# Remove .aspx, .php, .html .cfm if it exist
	if url.endswith(".aspx") or url.endswith(".php") or url.endswith(".html") or url.endswith(".shtml") \
			or url.endswith(".htm") or url.endswith(".cfm"):
		splitted_url = url.rsplit('/', 1)
		url = splitted_url[0]

	# Splitting urls for removing sub-URLs
	splitted_url = url.rsplit('/', 1)

	# Remove sub-URLs
	if "contact" in splitted_url[1]:
		url = splitted_url[0]

	elif "appointment" in splitted_url[1]:
		url = splitted_url[0]

	elif "hour" in splitted_url[1]:
		url = splitted_url[0]

	elif "location" in splitted_url[1]:
		url = splitted_url[0]

	elif "insurance" in splitted_url[1]:
		url = splitted_url[0]

	elif "info" in splitted_url[1]:
		url = splitted_url[0]

	elif "pages" in splitted_url[1]:
		url = splitted_url[0]

	elif "home" in splitted_url[1]:
		url = splitted_url[0]

	elif "home-page" in splitted_url[1]:
		url = splitted_url[0]

	elif "index" in splitted_url[1]:
		url = splitted_url[0]

	return url


# Find SHC URL given the university name
def get_shc_urls_from_uni_name(input_dataframe, keys, driver_path, cse_id, output_dir):
	header = ['University_name', 'University SHC URL']
	output_dataframe = pd.DataFrame(columns=header)

	# Split dataframe based on calculated number of keys
	input_dataframe_splitted = np.array_split(input_dataframe, len(keys))

	# Combine keys with split dataframe
	for every_split, my_api_key in zip(input_dataframe_splitted, keys):

		every_split = pd.DataFrame(every_split)
		i = 0

		for index, row in every_split.iterrows():

			url_found = 0

			output_dataframe_splitted = pd.DataFrame(columns=header)
			university = row["University_name"]
			print("- ", university)

			# Clean university name, replace special characters with space
			uni_name = re.sub("[!@#$%^&*()[]{};:,./<>?\|`~-=_+]", " ", university)

			# Construct the queries for the following searches
			uni_shc = uni_name + " student health center"
			uni_shc_web = google_search(uni_shc, my_api_key, cse_id, num=3, )  # consider 3 results

			if(uni_shc_web is not None):
			# Check if retrieved URL do not
				for result in uni_shc_web:
					url = result.get('link', 'none')

					# If url with .edu found
					if ('.edu' in url) and ('.pdf' not in url):
						# Get the redirected URL, remove sub-urls and store it in the dataframe
						redirected_url = get_redirected_url(url, driver_path)
						sanitized_url = remove_sub_urls(redirected_url)

						output_dataframe_splitted.loc[i] = [university, sanitized_url]
						url_found = 1
						break

			if url_found == 0:
				print("   - University SHC website not found!")
				output_dataframe_splitted.loc[i] = [university, "-1"]

			i = i + 1

			output_dataframe = pd.concat([output_dataframe, output_dataframe_splitted], sort=False)

	# Store result in output directory
	output_dataframe.to_csv(output_dir + '/University_SHC.csv')

	return output_dataframe
