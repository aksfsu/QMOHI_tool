"""
Complete generic pipeline
Input - File containing university names, keywords and Google API keys
Output - reading level and quantity metric
Argument - Input file in form of csv sheet along with absolute path with below columns -
1. University_name
2. Keywords
3. API_keys (Google API keys for custom search)
4. Custom search engine unique id
5. Selenium web driver for chrome
6. Output directory for storing results
7. Ideal document name with absolute path
"""
import sys
# sys.path.append(r'./qmomi')
import time
import datetime

from qmohi.src.input_parser import parse_input, get_uni_shc, sentence_extraction
from qmohi.src.data_prep import filter_relevant_data, webpage_crawling, store_webpages, \
	get_shc_webpages_with_keywords
from qmohi.src.metric_calc import reading_level, combine_results, metric_calculation1, metric_calculation2


# Execute complete pipeline
def execute(input_file_path):
	timestamp = time.time()
	date = datetime.datetime.fromtimestamp(timestamp)
	print("Start Overall:", date.strftime('%H:%M:%S.%f'))

	# Get user's input
	print("\n============ PHASE 1 =============\n")
	print("###### Reading input file ######")
	print("- Input file given by user: ", input_file_path)
	file = parse_input.read_input_file(input_file_path)

	# Set output directory for storing results
	print("- Setting up output directory: ", end="")
	output_dir = parse_input.set_output_directory(file)

	# Get university names from user input
	print("- Collecting input university names")
	universities_list, no_of_universities = parse_input.get_input_university_names(file)

	# Get keywords from user input
	print("- Collecting input keywords")
	keyword_list = parse_input.get_input_keywords(file)

	# Divide the keywords in sets to make query
	num_of_words, query_keywords = parse_input.divide_query_keywords(keyword_list)

	# Calculate minimum number of keys required
	no_of_keys_for_shc, no_of_keys_for_site_specific_search = parse_input.calculate_num_keys_required(
		no_of_universities,
		num_of_words)

	# Get API keys from user input
	print("- Collecting input API keys")
	keys_list, no_of_input_keys = parse_input.get_input_api_keys(file)

	# Check if API keys in the user's input are sufficient
	parse_input.are_input_api_keys_sufficient(no_of_keys_for_shc, no_of_keys_for_site_specific_search, no_of_input_keys)

	# Get Selenium web driver path from user input
	print("\n- Collecting input Selenium Web Driver", end="")
	driver_path = parse_input.get_input_webdriver(file)

	# Get CSE ID from user input
	print("- Collecting input CSE id", end="")
	cse_id = parse_input.get_input_cse(file)

	# Get ideal document path for ideal information on given keyword's topic
	print("- Collecting ideal document name", end="")
	ideal_doc = parse_input.get_ideal_document_with_path(file)

	# Get the pre-trained model for calculating similarity. If not provided, old method is used.
	print("- Collecting input model", end="")
	model_path = parse_input.get_model(file)

	# Get the margin for the sentence extraction. If not provided, the function returns the default value (=2)
	print("- Collecting sentence extraction margin", end="")
	sentence_extraction_margin = parse_input.get_sentence_extraction_margin(file)

	# Get university SHC from university name
	print("\n###### Finding university SHC websites ######")
	result_dataframe3 = get_uni_shc.get_shc_urls_from_uni_name(universities_list, keys_list[:no_of_keys_for_shc],
															   driver_path, cse_id, output_dir)

	# Get related web pages under SHC website having presence of input keywords
	print("\n============ PHASE 2 =============\n")
	print("###### Searching SHC web pages having presence of keywords ######")
	result_dataframe4 = get_shc_webpages_with_keywords.get_links(result_dataframe3, query_keywords, keys_list[
								0:no_of_keys_for_shc + no_of_keys_for_site_specific_search],
																 cse_id, output_dir)

	# Store web pages in html format
	print("\n###### Saving web pages locally in HTML format ######")
	store_webpages.save_webpage_content(result_dataframe4, output_dir)

	# Find anchor sentences and highlight them in html format
	sentence_extraction.get_search_results(output_dir, keyword_list, sentence_extraction_margin)
	
	# Get data from the urls found under shc
	print("\n###### Collecting all text data from SHC web pages found ######")
	result_dataframe5 = webpage_crawling.retrieve_content_from_urls(result_dataframe4, keyword_list,
																	output_dir, driver_path)

	# Find relevant content from retrieved website data
	print("\n###### Filtering information relevant to keywords ######")
	result_dataframe6, keyword_list, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary = filter_relevant_data.find_relevant_content(result_dataframe5, keyword_list, output_dir)

	print("\n###### Universities where keywords relevant information was found ######")
	print(result_dataframe6["University name"])

	# Calculate overall reading level of relevant content retrieved from the urls
	print("\n============ PHASE 3 =============\n")
	print("###### Calculating Readability metric ######")
	result_dataframe7 = reading_level.get_reading_level(result_dataframe6, output_dir)

	# Calculate quantity of keywords, Prevalence metric, Coverage metric
	print("\n###### Calculating quantity of keywords, Prevalence metric, Coverage metric ######")
	result_dataframe8 = metric_calculation1.metric_calculation(result_dataframe7, keyword_list, output_dir, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary)

	# Calculate Similarity metric, Objectivity metric, Polarity metric, Timeliness metric, Navigation metric
	print("\n###### Calculating Similarity metric, Objectivity metric, Polarity metric, Timeliness metric, Navigation metric ######")
	result_dataframe9 = metric_calculation2.calculate_metrics(result_dataframe6, output_dir, ideal_doc, driver_path, model_path)

	# Consolidating final result together
	print("\n###### Consolidating all metric values together ######")
	combine_results.combine_all_results_together(result_dataframe8, result_dataframe9, result_dataframe3, output_dir)
	timestamp = time.time()
	date = datetime.datetime.fromtimestamp(timestamp)
	print("End Overall:", date.strftime('%H:%M:%S.%f'))

	print("\n============ FINISHED =============\n")

if __name__ == "__main__":
	import sys
	execute(sys.argv[1])
