import urllib.request
import urllib.error
import urllib.parse
import os
import re


def save_webpage_content(input_dataframe, output_dir):
	# Create new directory inside output_directory for saving web pages
	if output_dir.endswith('/'):
		save_output_path = output_dir + "saved_webpages"
	else:
		save_output_path = output_dir + "/saved_webpages"

	os.makedirs(save_output_path)

	# For every university
	for index, row in input_dataframe.iterrows():

		university = row['University name']
		links = row['Keywords matched webpages on SHC']

		# Assigning directory location path every time
		save_output = save_output_path

		if save_output.endswith('/'):
			save_output = save_output + university
		else:
			save_output = save_output + '/' + university

		print("Output path = ", save_output)

		# Creating new directory for storing web pages of every university
		os.makedirs(save_output)

		# Only in case if you are reading input from a csv file
		if isinstance(links, str):
			links = re.findall(r"'(.*?)'", links)

		for i in range(len(links)):
			if links[i].endswith(".pdf") or links[i].endswith(".docx") or links[i].endswith(".doc"):
				print("Either pdf or doc ", links[i])

			else:
				try:
					webpage_index_name = save_output + '/' + str(i) + '.html'
					urllib.request.urlretrieve(links[i], webpage_index_name)
				except Exception as e:
					print("Error in saving webpage", e)
