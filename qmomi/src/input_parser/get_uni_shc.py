'''
Get university SHC from university name
input - list of university names
output - list of university SHCs
'''

from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
import sys
import datetime

# from selenium import RemoteWebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


## building Google custom search engine
def google_search(search_term, api_key, cse_id, **kwargs):
	try:
		service = build("customsearch", "v1", developerKey=api_key)
		res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
		return res['items']


	#
	# except TimeoutException as e:
	#
	#     print("timeout exception in selenium")

	except Exception as e:
		print("Error in google search : ", e)
		sys.exit()


##Get reciredcted URL with the help of headless browser and chromedriver
def get_redirected_url(url, driver_path):
	options = Options()
	options.add_argument("--headless")  # Runs Chrome in headless mode.

	# run web driver with the driver_path provided by user
	driver = webdriver.Chrome(driver_path, chrome_options=options)

	#######

	# driver = webdriver.Remote("http://127.0.0.1:4444/wd/hub", DesiredCapabilities.CHROME)

	#######

	try:  ## try getting redirected URL
		driver.get(url)
		redirected_url = driver.current_url
		return redirected_url

	except WebDriverException as e:

		print("Web driver exception in selenium :", e.msg)


	except exceptions as e:  ### if there is some error in URL redirection
		print("Error in URL redirection!")
		print(e.msg)

	return url


### removing sub-urls from the program retrieved URLs
def remove_sub_urls(url):
	##remove / in the end if it exist
	if url.endswith('/'):
		removed_slash = url.rsplit('/', 1)
		url = removed_slash[0]

	## remove .aspx, .php, .html .cfm if it exist
	if (url.endswith(".aspx") or url.endswith(".php") or url.endswith(".html")
			or url.endswith(".shtml") or url.endswith(".htm") or url.endswith(".cfm")):
		splitted_url = url.rsplit('/', 1)
		url = splitted_url[0]

	##splitting urls for removing sub-URLs
	splitted_url = url.rsplit('/', 1)

	## remove sub-URLs
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


##mfind SHC URL given the university name
def get_shc_urls_from_uni_name(input_dataframe, keys, driver_path, cse_id, output_dir):
	### timestamp extra added
	header = ['University_name', 'University SHC URL', 'timestamp']
	# header = ['University_name', 'University SHC URL']
	output_dataframe = pd.DataFrame(columns=header)

	## split dataframe based on calculated number of keys
	input_dataframe_splitted = np.array_split(input_dataframe, len(keys))

	# combine keys with splitted dataframe
	for every_split, my_api_key in zip(input_dataframe_splitted, keys):

		every_split = pd.DataFrame(every_split)
		i = 0
		print("Key : ", my_api_key)

		for index, row in every_split.iterrows():

			url_found = 0

			output_dataframe_splitted = pd.DataFrame(columns=header)
			university = row["University_name"]

			## clean university name
			uniName = re.sub("[!@#$%^&*()[]{};:,./<>?\|`~-=_+]", " ",
							 university)  # replace special characters with space

			# Construct the queries for the following searches
			uniSHC = uniName + " student health center"
			uniSHC_web = google_search(uniSHC, my_api_key, cse_id, num=3, )  # consider 3 results
			print("print query:", uniSHC)

			# check if retrieved URL do not
			for result in uniSHC_web:
				url = result.get('link', 'none')
				if ('.edu' in url) and ('.pdf' not in url):  ## if url with .edu found
					### get the redirected URL, remove sub-urls and store it in the dataframe
					redirected_url = get_redirected_url(url, driver_path)
					sanitized_url = remove_sub_urls(redirected_url)

					### timestamp extra added
					timestamp = datetime.datetime.now()
					output_dataframe_splitted.loc[i] = [university, sanitized_url, timestamp]
					# output_dataframe_splitted.loc[i] = [university, sanitized_url]
					url_found = 1
					break

			if url_found == 0:
				### timestamp extra added
				timestamp = datetime.datetime.now()
				output_dataframe_splitted.loc[i] = [university, "-1", timestamp]
				# output_dataframe_splitted.loc[i] = [university, "-1"]

			print(output_dataframe_splitted.loc[i])

			i = i + 1

			print("\n")

			output_dataframe = pd.concat([output_dataframe, output_dataframe_splitted], sort=False)

	output_dataframe.to_csv(output_dir + '/University_SHC.csv')  ### this overwrites complete dataframe everytime

	return output_dataframe
