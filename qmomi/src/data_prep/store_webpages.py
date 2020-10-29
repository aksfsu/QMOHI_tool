import urllib.request, urllib.error, urllib.parse
import os
import datetime
import pandas as pd
import re


def save_webpage_content(input_dataframe, output_dir):
	if output_dir.endswith('/'):
		save_output_path = output_dir + "saved_webpages"

	else:
		save_output_path = output_dir + "/saved_webpages"

	os.makedirs(save_output_path)

	##for every university
	for index, row in input_dataframe.iterrows():

		university = row['University name']
		links = row['Keywords matched webpages on SHC']

		save_output = save_output_path  ## assigning directory location path every time

		if save_output.endswith('/'):
			save_output = save_output + university
		else:
			save_output = save_output + '/' + university

		print("Output path = ", save_output)

		# creating new directory for storing webpages of every university
		os.makedirs(save_output)

		# links = re.findall(r"'(.*?)'", links)  ### only in case if you are reading input from a csv file
		for i in range(len(links)):

			if links[i].endswith(".pdf") or links[i].endswith(".docx") or links[i].endswith(".doc"):
				print("Either pdf or doc ", links[i])
			# continue

			else:
				try:
					webpage_index_name = save_output + '/' + str(i) + '.html'
					urllib.request.urlretrieve(links[i], webpage_index_name)
				except Exception as e:
					print("Error in saving webpage", e)


'''input_dataframe = pd.read_csv("/Users/tejasvibelsare/Desktop/Output 2020-05-19 10:53:13/keywords_matched_webpages_on_SHC.csv")
output_dir = "/Users/tejasvibelsare/Desktop/Output 2020-05-19 10:53:13/saved_webpages"
save_webpage_content(input_dataframe, output_dir)
'''
