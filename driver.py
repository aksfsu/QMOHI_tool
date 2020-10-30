"""
Complete generic pipeline
Input - File containing university names, keywords and Google API keys
Output - reading level and quantity metric
Argument - Input file in form of excel sheet along with absolute path with below columns -
1. University_name
2. Keywords
3. API_keys (Google API keys for custom search)
4. Custom search engine unique id
5. Selenium webdriver for chrome
"""

from qmomi.src.input_parser import get_uni_shc, parse_input
from qmomi.src.data_prep import filter_relevant_data, webpage_crawling, get_shc_webpages_with_keywords, store_webpages
from qmomi.src.metric_calc import metric_calculation2, combine_results, metric_calculation1, reading_level


# Execute complete pipeline
def execute(input_file_path):
	# Get user's input
	file = parse_input.read_input_file(input_file_path)

	# Set output directory for storing results
	output_dir = parse_input.set_output_directory(file)

	# Get university names from user input
	universities_list, no_of_universities = parse_input.get_input_university_names(file)

	# Get keywords from user input
	keyword_list = parse_input.get_input_keywords(file)

	# Divide the keywords in sets to make query
	num_of_words, query_keywords = parse_input.divide_query_keywords(keyword_list)

	# Calculate minimum number of keys required
	no_of_keys_for_shc, no_of_keys_for_site_specific_search = parse_input.calculate_num_keys_required(
		no_of_universities,
		num_of_words)

	# Get API keys from user input
	keys_list, no_of_input_keys = parse_input.get_input_api_keys(file)

	# Check if API keys in the user's input are sufficient
	parse_input.are_input_api_keys_sufficient(no_of_keys_for_shc, no_of_keys_for_site_specific_search, no_of_input_keys)

	# Get Selenium web driver path from user input
	driver_path = parse_input.get_input_webdriver(file)

	# Get CSE ID from user input
	cse_id = parse_input.get_input_cse(file)

	# Get ideal document path for ideal information on given keyword's topic
	ideal_doc = parse_input.get_ideal_document_with_path(file)

	# Get university SHC from university name
	result_dataframe3 = get_uni_shc.get_shc_urls_from_uni_name(universities_list, keys_list[:no_of_keys_for_shc],
																	driver_path, cse_id, output_dir)

	# Get related web pages under SHC website having presence of input keywords
	result_dataframe4 = get_shc_webpages_with_keywords.get_links(result_dataframe3, query_keywords, keys_list[
								no_of_keys_for_shc:no_of_keys_for_shc + no_of_keys_for_site_specific_search],
								cse_id, output_dir)

	# Store web pages in html format
	store_webpages.save_webpage_content(result_dataframe4, output_dir)

	# Get data from the urls found under shc
	result_dataframe5 = webpage_crawling.retrieve_content_from_urls(result_dataframe4, keyword_list,
																	output_dir, driver_path)

	# Find relevant content from retrieved website data
	result_dataframe6, keyword_list = filter_relevant_data.find_relevant_content(result_dataframe5, keyword_list, output_dir)

	# Calculate overall reading level of relevant content retrieved from the urls
	result_dataframe7 = reading_level.get_reading_level(result_dataframe6, output_dir)

	# Calculate quantity of keywords, Prevalence metric, Coverage metric
	result_dataframe8 = metric_calculation1.metric_calculation(result_dataframe7, keyword_list, output_dir)

	# Calculate Similarity metric, Objectivity metric, Polarity metric, Timeliness metric, Navigation metric
	result_dataframe9 = metric_calculation2.calculate_metrics(result_dataframe6, output_dir, ideal_doc, driver_path)

	# Consolidating final result together
	combine_results.combine_all_results_together(result_dataframe8, result_dataframe9, result_dataframe3, output_dir)
