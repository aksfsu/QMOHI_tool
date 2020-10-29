'''
Finds links under given SHC having presence of given keywords
Input - University SHC URl, list of keywords and Google API keys
Output - All the links under University SHC containing the given keywords
'''

import json
import pandas as pd
import numpy as np
import time
import datetime

from googleapiclient.discovery import build


class SHC_URL:

	def __init__(self, url, api_key, cse_id):

		self.url = url  ## get url from array (string)
		self.api_key = api_key
		self.cse_id = cse_id

	####get links with given keywords
	def get_links_with_keywords(self, keywords):

		links = []
		print("Given SHC URL is : " + self.url)

		##preparing query with the given keywords
		for keyword in keywords:
			query = " " + keyword + " site:" + self.url + " "


			print(query)

			##Google API custom search service
			time.sleep(1)

			try:
				service = getService(self.api_key)
				response = service.cse().list(
					q=query,
					cx=self.cse_id,
					lr='lang_en',
				).execute()


				##output received in the form of json
				with open('data.json', 'w') as outfile:
					json.dump(response, outfile)

				##items contain all the retrieved results
				if not 'items' in response:
					print('No result !!\nres is: {}'.format(response))

				else:
					print("Total results found : ", len(response['items']))
					for item in response['items']:
						links.append(item['link'])  ## links from the items contain URLs

			except Exception as e:
				print("Caught exception for Custom Search engine!", e)

		links = list(dict.fromkeys(links))
		print(links)
		return links


### building custom search engine with given keys
def getService(api_key):
	service = build("customsearch", "v1", developerKey=api_key)

	return service


### get relevant URLs by custom search with keywords and SHC site
def get_links(input_dataframe, keywords, keys, cse_id, output_dir):
	header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC',
			  'Keywords matched webpages on SHC', 'start_timestamp', 'end_timestamp']
	output_dataframe = pd.DataFrame(columns=header)

	## split dataframe based on calculated number of keys
	input_dataframe_splitted = np.array_split(input_dataframe, len(keys))

	###combine keys with splitted dataframe
	for every_split, my_api_key in zip(input_dataframe_splitted, keys):
		every_split = pd.DataFrame(every_split)
		i = 0

		## for every university in the split
		for index, row in every_split.iterrows():

			start_timestamp = datetime.datetime.now()
			output_dataframe_splitted = pd.DataFrame(columns=header)
			university = row['University_name']
			shc = row['University SHC URL']

			if shc != -1:  ##if SHC URL was found
				url_obj = SHC_URL(shc, my_api_key, cse_id)
				links_shc_website = url_obj.get_links_with_keywords(keywords)
				end_timestamp = datetime.datetime.now()
				output_dataframe_splitted.loc[i] = [university, shc, int(len(links_shc_website)), links_shc_website, start_timestamp, end_timestamp]

			i = i + 1


			print("\n")

			output_dataframe = pd.concat([output_dataframe, output_dataframe_splitted],
										 sort=False)  #### Concatenating current dataframe with overall result

	output_dataframe.to_csv(output_dir + '/keywords_matched_webpages_on_SHC.csv')  ### storing overall results

	return output_dataframe
