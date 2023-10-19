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
7. Comparison document name with absolute path
"""
import sys
# sys.path.append(r'./qmomi')
import time
import datetime

from qmohi.src.input_parser import parse_input, get_uni_shc
from qmohi.src.data_prep import filter_relevant_data, store_webpages, get_shc_webpages_with_keywords
from qmohi.src.metric_calc import combine_results, metric_calculation1, metric_calculation2
from qmohi.src.metric_calc.readability_metric import reading_level


# Execute complete pipeline
def execute(input_file_path):
	timestamp = time.time()
	date = datetime.datetime.fromtimestamp(timestamp)
	print("Start: ", date.strftime('%H:%M:%S.%f'))

	# Get user's input
	print("\n============ PHASE 1 =============\n")
	print("Collecting the parameters from the input file...")
	# print("- Input file given by user: ", input_file_path)
	file = parse_input.read_input_file(input_file_path)

	# Set output directory for storing results
	# print("- Setting up output directory: ", end="")
	output_dir = parse_input.set_output_directory(file)

	# Get university names from user input
	# print("- Collecting input university names")
	universities_list, no_of_universities = parse_input.get_input_university_names(file)

	# Get API keys from user input
	# print("- Collecting input API keys")
	keys_list = parse_input.get_input_api_keys(file, 0, 0, force_pass=True)

	# Get CSE ID from user input
	# print("- Collecting input CSE id", end="")
	cse_id = parse_input.get_input_cse(file)

	# Get keywords and the comparison document path from user input
	# print("- Collecting input keywords")
	keyword_list, comparison_doc_path = parse_input.review_input_keywords(input_file_path, file, keys_list, cse_id, output_dir)
	print(f'{keyword_list}, {comparison_doc_path}')

	# Divide the keywords in sets to make query
	num_of_words, query_keywords = parse_input.divide_query_keywords(keyword_list)

	# Calculate minimum number of keys required
	no_of_keys_for_shc, no_of_keys_for_site_specific_search = parse_input.calculate_num_keys_required(no_of_universities, num_of_words)

	# Get API keys from user input
	# print("- Collecting input API keys")
	keys_list_for_shc, keys_list_for_site_specific_search = parse_input.get_input_api_keys(file, no_of_keys_for_shc, no_of_keys_for_site_specific_search)

	# Get Selenium web driver path from user input
	# print("\n- Collecting input Selenium Web Driver", end="")
	driver_path = parse_input.get_input_webdriver(file)

	# Get the pre-trained model for calculating similarity. If not provided, old method is used.
	# print("- Collecting input model", end="")
	model_path = parse_input.get_model(file)

	# Get the margin for the sentence extraction. If not provided, the function returns the default value (=2)
	# print("- Collecting sentence extraction margin", end="")
	margin = parse_input.get_sentence_extraction_margin(file)

	readability_model_path = parse_input.get_readability_model(file)

	# Get university SHC from university name
	print("\nFinding university SHC websites...")
	shc_websites_df = get_uni_shc.get_shc_urls_from_uni_name(universities_list, keys_list_for_shc, driver_path, cse_id, output_dir)

	# Get related web pages under SHC website having presence of input keywords
	print("\n============ PHASE 2 =============\n")
	print("Searching SHC web pages having presence of keywords...")
	relevant_shc_webpages_df = get_shc_webpages_with_keywords.get_links(shc_websites_df, query_keywords, keys_list_for_site_specific_search, cse_id, output_dir)

	# Store web pages in html format
	print("\nSaving web pages on local computer...")
	store_webpages.save_webpage_content(relevant_shc_webpages_df, output_dir)

	# Find relevant content from retrieved website data
	print("\nFiltering information relevant to keywords...")
	topical_content_df, keyword_list, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary = filter_relevant_data.find_relevant_content(relevant_shc_webpages_df, keyword_list, margin, output_dir)

	# Calculate overall reading level of relevant content retrieved from the urls
	print("\n============ PHASE 3 =============\n")
	print("Calculating Readability metric...")
	reading_level_df = reading_level.get_reading_level(topical_content_df, output_dir, readability_model_path)

	# Calculate quantity of keywords, Prevalence metric, Coverage metric
	print("\nCalculating quantity of keywords, Prevalence metric, Coverage metric...")
	metrics1_df = metric_calculation1.metric_calculation(reading_level_df, keyword_list, output_dir, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary)

	# Calculate Similarity metric, Objectivity metric, Polarity metric, Timeliness metric, Navigation metric
	print("\nCalculating Similarity metric, Objectivity metric, Polarity metric, Timeliness metric, Navigation metric...")
	metrics2_df = metric_calculation2.calculate_metrics(topical_content_df, output_dir, comparison_doc_path, driver_path, model_path)

	# Consolidating final result together
	print("\nConsolidating all metric values together...")
	combine_results.combine_all_results_together(metrics1_df, metrics2_df, shc_websites_df, output_dir)
	timestamp = time.time()
	date = datetime.datetime.fromtimestamp(timestamp)
	print("End: ", date.strftime('%H:%M:%S.%f'))

	print("\n============ FINISHED =============\n")

if __name__ == "__main__":
	import sys
	execute(sys.argv[1])
