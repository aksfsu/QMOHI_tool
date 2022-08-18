import sys
import datetime
import os
import pandas as pd


def read_input_file(path):
	# Read the content from user's input file
	try:
		file = pd.read_csv(path,
							 usecols=['University_name', 'Keywords', 'API_keys', 'Paid_API_key', 'CSE_id', 'Selenium_Chrome_webdriver',
									  'Output_directory', 'Ideal_document', 'Word_vector_model', 'Sentence_extraction_margin'])
	except Exception as e:
		print(e)
		print("Problem with input file! Make sure the location of the file is correct and columns are "
			  "'University_name', 'Keywords', 'API_keys', 'Paid_API_key', 'CSE_id', 'Selenium_Chrome_webdriver', 'Output_directory', 'Ideal_document', 'Word_vector_model'. ")
		sys.exit()

	return file


def set_output_directory(file):
	# Output directory for storing results
	output_dir = file[['Output_directory']].copy()
	# Dropping rows with NaN values
	output_dir = output_dir.dropna(axis=0, how='any')

	if output_dir.empty:
		print("Please provide output directory to store the results!")
		sys.exit()

	output_dir = output_dir['Output_directory'].values[0]
	if not os.access(output_dir, os.W_OK):
		print(output_dir)
		print("Either provided output directory do not exist or it do not have write access for this program!")
		sys.exit()

	# Creating new directory inside given output path to store results
	now = datetime.datetime.now()
	if output_dir.endswith('/'):
		output_dir = output_dir + 'Output ' + now.strftime("%Y-%m-%d %H:%M:%S")
	else:
		output_dir = output_dir + '/Output ' + now.strftime("%Y-%m-%d %H:%M:%S")

	os.makedirs(output_dir)

	return output_dir


def get_input_university_names(file):
	# Reading university names provided by user
	universities_list = file[['University_name']].copy()
	# Dropping rows with NaN values
	universities_list = universities_list.dropna(axis=0, how='any')

	if universities_list.empty:
		print("Please provide university names!")
		sys.exit()

	print(universities_list, "\n")
	no_of_universities = universities_list.University_name.count()

	return universities_list, no_of_universities


def get_input_keywords(file):
	# Reading keywords provided by user
	keywords = file[['Keywords']].copy()
	# Dropping rows with NaN values
	keywords = keywords.dropna(axis=0, how='any')

	if keywords.empty:
		print("Please provide keywords to look for!")
		sys.exit()

	# Stripping extra leading and trailing spaces in the keywords
	keywords = keywords.apply(lambda x:x.str.strip())

	# Stripping extra spaces between keywords
	keywords = keywords.apply(lambda x:x.str.replace(' +', ' '))

	# Convert keywords into lower case
	keywords = keywords.apply(lambda x:x.str.lower())

	# Creating list of keywords to pass it as required
	keyword_list = keywords['Keywords'].tolist()

	print(keywords, "\n")
	return keyword_list


def divide_query_keywords(keyword_list):
	num_of_words = 0
	keyword_list_dict = {}

	# Dividing keyword_list in sub-lists (in dictionary) such that sub-lists will contain keywords having word count <= 26
	for my_keyword in keyword_list:
		num_of_words += len(my_keyword.split())
		num_index = (num_of_words // 26) + 1
		keyword_list_dict.setdefault(num_index, []).append(my_keyword)

	# Making list of dictionary values
	list_query_keywords = list(keyword_list_dict.values())

	# Join keywords for the API query
	query_keywords = []
	for each_query in list_query_keywords:
		each_query = '" | "'.join(each_query)
		query_keywords.append('"{0}"'.format(each_query))

	return num_of_words, query_keywords


def calculate_num_keys_required(no_of_universities, num_of_words):
	# Assuming daily limit of 90 queries per API key just to be on safer side
	no_of_keys_for_shc = (no_of_universities // 90) + 1

	# Assuming daily limit of 90 queries per API key and maximum 6 words in university name
	no_of_keys_for_site_specific_search = ((((num_of_words // 26) + 1) * no_of_universities) // 90) + 1
	return no_of_keys_for_shc, no_of_keys_for_site_specific_search


def get_input_api_keys(file, no_of_keys_for_shc, no_of_keys_for_site_specific_search):
	# Reading API keys provided by user
	keys = file[['Paid_API_key']].copy()
	# Dropping rows with NaN values
	keys = keys.dropna(axis=0, how='any')
	no_of_keys = keys.Paid_API_key.count()

	if no_of_keys > 0:
		print(keys['Paid_API_key'])
		# Creating list of keys to pass it as required
		return keys['Paid_API_key'].tolist()

	else:
		# Reading API keys provided by user
		keys = file[['API_keys']].copy()
		# Dropping rows with NaN values
		keys = keys.dropna(axis=0, how='any')
		no_of_keys = keys.API_keys.count()
		are_input_api_keys_sufficient(no_of_keys_for_shc, no_of_keys_for_site_specific_search, no_of_keys)
		print(keys['API_keys'])

	# Creating list of keys to pass it as required
	return keys['API_keys'].tolist()


def are_input_api_keys_sufficient(no_of_keys_for_shc,
								  no_of_keys_for_site_specific_search,
								  no_of_input_keys):
	no_of_keys_required = max(no_of_keys_for_shc, no_of_keys_for_site_specific_search)
	# Checking if number of API keys provided by user are sufficient
	if no_of_input_keys < no_of_keys_required:
		print(f"For given universities and keywords, we need {no_of_keys_required} Google API keys. In the given input "
			  f"file only {no_of_input_keys} have been provided.")
		# Exit the program if not enough API keys
		sys.exit()


def get_input_webdriver(file):
	# Reading chrome driver provided by user
	webdriver = file[['Selenium_Chrome_webdriver']].copy()
	# Dropping rows with NaN values
	webdriver = webdriver.dropna(axis=0, how='any')

	if webdriver.empty:
		print("Please provide Selenium Chrome webdriver's absolute path with name!")
		sys.exit()

	driver_path = webdriver['Selenium_Chrome_webdriver'].values[0]
	print(": ", driver_path)
	return driver_path


def get_input_cse(file):
	# Reading CSE IDs provided by user
	cse = file[['CSE_id']].copy()
	# Dropping rows with NaN values
	cse = cse.dropna(axis=0, how='any')

	if cse.empty:
		print("Please provide CSE id!")
		sys.exit()

	cse_id = cse['CSE_id'].values[0]
	print(": ", cse_id)
	return cse_id


def get_ideal_document_with_path(file):
	# Reading ideal document path provided by user
	cse = file[['Ideal_document']].copy()
	# Dropping rows with NaN values
	cse = cse.dropna(axis=0, how='any')

	if cse.empty:
		print("Please provide ideal document to calculate similarity!")
		sys.exit()

	ideal_doc = cse['Ideal_document'].values[0]
	print(": ", ideal_doc)
	return ideal_doc

def get_model(file):
	# Reading the word vector model provided by user
	model_dir = file[['Word_vector_model']].copy()

	model_dir = model_dir.dropna(axis=0, how='any')

	if model_dir.empty:
		print("Please provide a model for calculating similarity!")
		sys.exit()

	model_dir = model_dir['Word_vector_model'].values[0]

	return model_dir

def get_sentence_extraction_margin(file):
	# Reading the margin for sentence extraction provided by user
	margin = file[['Sentence_extraction_margin']].copy()

	margin = margin.dropna(axis=0, how='any')

	if margin.empty:
		# Set the default value
		margin = 2

	margin = int(margin['Sentence_extraction_margin'].values[0])

	return margin
