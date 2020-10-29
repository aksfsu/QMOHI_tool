import pandas as pd
import sys
import datetime
import os


def read_input_file(path):
	try:  ### get the content from user's input file
		file = pd.read_excel(path,
							 usecols=['University_name', 'Keywords', 'API_keys', 'CSE_id', 'Selenium_Chrome_webdriver',
									  'Output_directory', 'Ideal_document_name_with_absolute_path'])  # reading input given by user
	# file = pd.read_excel(os.environ['input_file_path'], usecols=['University_name', 'Keywords', 'API_keys', 'CSE_id', 'Selenium_Chrome_webdriver', 'Output_directory'])  # reading input given by user)
	# file = pd.read_excel("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/Code/Generic_new/data/input_file.xlsx",
	# file=pd.read_excel(sys.argv[0],
	#					 usecols=['University_name', 'Keywords', 'API_keys', 'CSE_id', 'Selenium_Chrome_webdriver',
	#							  'Output_directory'])  # reading input given by user)
	except Exception as e:
		print(e)
		print("Problem with input file! Make sure the location of the file is correct and columns are "
			  "'University_name', 'Keywords', 'API_keys', 'CSE_id', 'Selenium_Chrome_webdriver', 'Output_directory. ")
		sys.exit()

	return file


def set_output_directory(file):

	output_dir = file[['Output_directory']].copy()  # reading output directory given by user to store the results
	output_dir = output_dir.dropna(axis=0, how='any')

	if output_dir.empty == True:
		print("Please provide output directory to store the results!")
		sys.exit()

	output_dir = output_dir['Output_directory'].values[0]
	if not os.access(output_dir, os.W_OK):
		print("Either provided output directory do not exist or it do not have write access for this program!")
		sys.exit()

	# creating new directory to store results
	now = datetime.datetime.now()

	if output_dir.endswith('/'):
		output_dir = output_dir + 'Output ' + now.strftime("%Y-%m-%d %H:%M:%S")
	else:
		output_dir = output_dir + '/Output ' + now.strftime("%Y-%m-%d %H:%M:%S")

	print("Output path = ", output_dir)
	os.makedirs(output_dir)  ### creating directory inside given output path by user for storing results

	return output_dir


def get_input_university_names(file):

	universities_list = file[['University_name']].copy()  # reading university names provided by user
	universities_list = universities_list.dropna(axis=0, how='any')  # dropping rows with NaN values

	if universities_list.empty == True:
		print("Please provide university names!")
		sys.exit()

	no_of_universities = universities_list.University_name.count()

	return universities_list, no_of_universities


def get_input_keywords(file):

	keywords = file[['Keywords']].copy()  # reading keywords provided by user
	keywords = keywords.dropna(axis=0, how='any')  # dropping rows with NaN values

	if keywords.empty == True:
		print("Please provide keywords to look for!")
		sys.exit()

	keyword_list = keywords['Keywords'].tolist()  ### creating list of keywords to pass it as required

	return keyword_list


def divide_query_keywords(keyword_list):
	num_of_words = 0
	keyword_list_dict = {}

	#### dividing keyword_list in sublists (in dictionary) such that sublists will contain keywords having word count <= 26
	for my_keyword in keyword_list:
		num_of_words += len(my_keyword.split())
		num_index = (num_of_words // 26) + 1
		keyword_list_dict.setdefault(num_index, []).append(my_keyword)

	# making list of dictionary values
	divide_query_keywords = list(keyword_list_dict.values())

	query_keywords = []
	#### join keywords for the API query
	for each_query in divide_query_keywords:
		each_query = '" | "'.join(each_query)
		query_keywords.append('"{0}"'.format(each_query))

	return num_of_words, query_keywords


def calculate_num_keys_required(no_of_universities, num_of_words):

	### assuming daily limit of 90 queries per API key just to be on safer side
	no_of_keys_for_shc = (no_of_universities // 90) + 1

	### assuming daily limit of 90 queries per API key and maximum 6 words in university name
	no_of_keys_for_site_specific_search = ((((num_of_words // 26) + 1) * no_of_universities) // 90) + 1

	return no_of_keys_for_shc, no_of_keys_for_site_specific_search


def get_input_api_keys(file):

	keys = file[['API_keys']].copy()  # reading API keys provided by user
	keys = keys.dropna(axis=0, how='any')  # dropping rows with NaN values
	no_of_keys = keys.API_keys.count()

	# return no_of_keys

	# # Checking if number of API keys provided by user are sufficient
	# if no_of_keys < 2:
	# 	print("Minimum 2 Google API keys are required for running this program!")
	# 	sys.exit()  ## exit the program if not enough API keys
	#
	# # possible count of universities to find result with given number of keys
	# elif no_of_keys < no_of_keys_required:
	#
	# 	possible_uni_count = no_of_keys / ((num_of_words // 26) + 2)
	# 	print("For given universities and keywords, we need " + (no_of_keys_required) + " Google API keys."
	# 		"In the given input file only " + no_of_keys + " have been provided. With these many keys we can get result for "
	# 		  + possible_uni_count + "universities")
	#
	# 	# Recalculating for limited number of universities
	# 	universities_list = universities_list.head(possible_uni_count)
	# 	no_of_universities = universities_list.University_name.count()
	# 	no_of_keys_for_shc = (no_of_universities // 90) + 1
	# 	no_of_keys_for_site_specific_search = ((((num_of_words // 26) + 1) * no_of_universities) // 90) + 1

	keys_list = keys['API_keys'].tolist()  ### creating list of keys to pass it as required
	return keys_list, no_of_keys


def are_input_api_keys_sufficient(no_of_keys_for_shc, no_of_keys_for_site_specific_search, no_of_input_keys, num_of_words, universities_list):

	no_of_keys_required = no_of_keys_for_shc + no_of_keys_for_site_specific_search
	# Checking if number of API keys provided by user are sufficient
	if no_of_input_keys < 2:
		print("Minimum 2 Google API keys are required for running this program!")
		sys.exit()  ## exit the program if not enough API keys

	# possible count of universities to find result with given number of keys
	elif no_of_input_keys < no_of_keys_required:

		possible_uni_count = no_of_input_keys / ((num_of_words // 26) + 2)
		print("For given universities and keywords, we need " + (no_of_keys_required) + " Google API keys."
			"In the given input file only " + no_of_input_keys + " have been provided. With these many keys we can get result for "
			  + possible_uni_count + "universities")

		# Recalculating for limited number of universities
		universities_list = universities_list.head(possible_uni_count)
		no_of_universities = universities_list.University_name.count()
		no_of_keys_for_shc = (no_of_universities // 90) + 1
		no_of_keys_for_site_specific_search = ((((num_of_words // 26) + 1) * no_of_universities) // 90) + 1

	return no_of_keys_for_shc, no_of_keys_for_site_specific_search


def get_input_webdriver(file):

	webdriver = file[['Selenium_Chrome_webdriver']].copy()  # reading chrome driver provided by user
	webdriver = webdriver.dropna(axis=0, how='any')  # dropping rows with NaN values

	if webdriver.empty == True:
		print("Please provide Selenium Chrome webdriver's absolute path with name!")
		sys.exit()

	driver_path = webdriver['Selenium_Chrome_webdriver'].values[0]

	return driver_path


def get_input_cse(file):
	cse = file[['CSE_id']].copy()  # reading university names provided by user
	cse = cse.dropna(axis=0, how='any')

	if cse.empty == True:
		print("Please provide CSE id!")
		sys.exit()

	cse_id = cse['CSE_id'].values[0]

	return cse_id


def get_ideal_document_with_path(file):
	cse = file[['Ideal_document_name_with_absolute_path']].copy()  # reading university names provided by user
	cse = cse.dropna(axis=0, how='any')

	if cse.empty == True:
		print("Please provide ideal document to calculate similarity!")
		sys.exit()

	ideal_doc = cse['Ideal_document_name_with_absolute_path'].values[0]

	return ideal_doc