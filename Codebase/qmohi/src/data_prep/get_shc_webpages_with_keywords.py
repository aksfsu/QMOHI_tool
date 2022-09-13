"""
Finds links under given SHC having presence of given keywords
Input - University SHC URl, list of keywords and Google API keys
Output - All the links under University SHC containing the given keywords
"""

from qmohi.src.input_parser.input_helper.cse_handler import CSEHandler
import pandas as pd
import numpy as np
import datetime

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
				url_obj = CSEHandler(my_api_key, cse_id)
				link_data = []
				for keyword in keywords:
					link_data += url_obj.get_links_by_query(shc, keyword)
				end_timestamp = datetime.datetime.now()
				output_dataframe_splitted.loc[i] = [university, shc, int(len(link_data)), link_data, start_timestamp, end_timestamp]

			i += 1

			# Concatenating current dataframe with overall result
			output_dataframe = pd.concat([output_dataframe, output_dataframe_splitted], sort=False)
			
	# Storing overall results
	output_dataframe.to_csv(output_dir + '/keywords_matched_webpages_on_SHC.csv')

	return output_dataframe
