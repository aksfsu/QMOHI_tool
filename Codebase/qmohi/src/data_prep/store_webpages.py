import urllib.request
import urllib.error
import urllib.parse
from os import makedirs
from os.path import join


def save_webpage_content(input_dataframe, output_dir):
	# Create new directory inside output_directory for saving web pages
	save_output_path = join(output_dir, "saved_webpages")
	makedirs(save_output_path)
	print(f"Path to the saved web pages: {save_output_path}")

	# For every university
	for _, row in input_dataframe.iterrows():
		university = row['University name']
		link_data = row['Keywords matched webpages on SHC']

		# Assigning directory location path every time
		save_output = join(save_output_path, university)

		# Creating new directory for storing web pages of every university
		makedirs(save_output, exist_ok=True)

		for i in range(len(link_data)):
			try:
				opener = urllib.request.build_opener()
				opener.addheaders = [('User-Agent', 'Mozilla/5.0')] #chromedirver/selenuim
				urllib.request.install_opener(opener)
				webpage_index_name = join(save_output, str(i) + '.' + link_data[i]["format"])
				urllib.request.urlretrieve(link_data[i]["url"], webpage_index_name)
			except Exception as e:
				print("Error in saving one of the web page for ", university)
				print(link_data[i]["url"], " : ", e)
