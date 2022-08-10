"""
Finds links under given SHC having presence of given keywords
Input - University SHC URl, list of keywords and Google API keys
Output - All the links under University SHC containing the given keywords
"""

from googleapiclient.discovery import build
import json
import pandas as pd
import numpy as np
import time
import datetime


class ShcUrl:

	def __init__(self, url, api_key, cse_id):
		self.url = url
		self.api_key = api_key
		self.cse_id = cse_id

	# Get links with given keywords
	def get_link_data_with_keywords(self, keywords):
		links = []

		# Preparing query with the given keywords
		for keyword in keywords:
			query = " " + keyword + " site:" + self.url + " "

			# Google API custom search service
			time.sleep(1)
			try:
				service = get_service(self.api_key)
				response = service.cse().list(
					q=query,
					cx=self.cse_id,
					lr='lang_en',
				).execute()

				# Output received in the form of json
				with open('data.json', 'w') as outfile:
					json.dump(response, outfile)

				# Items contain all the retrieved results
				if 'items' not in response:
					print("   - No web pages found!")

				else:
					for item in response['items']:
						if item['link'].endswith(".pdf"):
							content_format = 'pdf'
						elif 'mime' in item and 'pdf' in item['mime'].lower():
							content_format = 'pdf'
						elif 'fileFormat' in item and 'pdf' in item['fileFormat'].lower():
							content_format = 'pdf'
						else:
							content_format = 'html'
						
						# Links from the items contain URLs
						links.append({'url': item['link'], 'format': content_format})

			except Exception as e:
				print("Caught exception for Custom Search engine!", e)

		return links


# Building custom search engine with given keys
def get_service(api_key):
	return build("customsearch", "v1", developerKey=api_key)


# Get relevant URLs by custom search with keywords and SHC site
def get_links(input_dataframe, keywords, keys, cse_id, output_dir):
	header = ['University name', 'University SHC URL', 'Count of SHC webpages matching keywords',
			  'Keywords matched webpages on SHC', 'start_timestamp', 'end_timestamp']
	output_dataframe = pd.DataFrame(columns=header)

	# Split dataframe based on calculated number of keys
	input_dataframe_splitted = np.array_split(input_dataframe, len(keys))

	# Combine keys with split dataframe
	for every_split, my_api_key in zip(input_dataframe_splitted, keys):
		every_split = pd.DataFrame(every_split)
		i = 0

		# For every university in the split
		for index, row in every_split.iterrows():
			start_timestamp = datetime.datetime.now()
			output_dataframe_splitted = pd.DataFrame(columns=header)
			university = row['University_name']
			shc = row['University SHC URL']
			print("- ", university)

			# If SHC URL was found
			if shc:
				url_obj = ShcUrl(shc, my_api_key, cse_id)
				link_data = url_obj.get_link_data_with_keywords(keywords)
				link_data = [link for link in url_obj.get_link_data_with_keywords(keywords) if not link["url"].endswith(".docx") and not link["url"].endswith(".doc")]
				end_timestamp = datetime.datetime.now()
				output_dataframe_splitted.loc[i] = [university, shc, int(len(link_data)), link_data, start_timestamp, end_timestamp]

			i += 1

			# Concatenating current dataframe with overall result
			output_dataframe = pd.concat([output_dataframe, output_dataframe_splitted], sort=False)
			
	# Storing overall results
	output_dataframe.to_csv(output_dir + '/keywords_matched_webpages_on_SHC.csv')

	return output_dataframe
