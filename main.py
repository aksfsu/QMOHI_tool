'''Complete generic pipeline
input - File containing university names, keywords and Google API keys
output - reading level and quantity metric
argument - Input file in form of excel sheet along with absolute path
with 3 columns -
1. University_name
2. Keywords
3. API_keys (Google API keys for custom search)
4. Custom search engine unique id
5. Selenium webdriver for chrome
'''

from qmomi.src.input_parser import get_uni_shc, parse_input
from qmomi.src.data_prep import filter_relevant_data, webpage_crawling, get_shc_webpages_with_keywords
from qmomi.src.metric_calc import metric_calculation, combine_results, quantity_metrics, reading_level

import datetime


def main():

	start_time = datetime.datetime.now()

	print("Start time :", start_time)

	file = parse_input.read_input_file(sys.argv[1])

	print(file)

	output_dir = parse_input.set_output_directory(file)

	universities_list, no_of_universities = parse_input.get_input_university_names(file)

	keyword_list = parse_input.get_input_keywords(file)

	num_of_words, query_keywords = parse_input.divide_query_keywords(keyword_list)

	no_of_keys_for_shc, no_of_keys_for_site_specific_search = parse_input.calculate_num_keys_required(no_of_universities, num_of_words)

	keys_list, no_of_input_keys = parse_input.get_input_api_keys(file)

	no_of_keys_for_shc, no_of_keys_for_site_specific_search = parse_input.are_input_api_keys_sufficient(no_of_keys_for_shc, no_of_keys_for_site_specific_search, no_of_input_keys, num_of_words, universities_list)

	driver_path = parse_input.get_input_webdriver(file)

	cse_id = parse_input.get_input_cse(file)

	ideal_doc = parse_input.get_ideal_document_with_path(file)


	# get university SHC from university name
	result_dataframe3 = get_uni_shc.get_shc_urls_from_uni_name(universities_list,
																				keys_list[:no_of_keys_for_shc],
															   driver_path, cse_id, output_dir)
	#
	# result_dataframe3 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/superset/Output 2020-09-15 11:36:34/University_SHC.csv")
	uni_shc_time = datetime.datetime.now()

	### get related links under shc with given keywords
	result_dataframe4 = get_shc_webpages_with_keywords.get_links(result_dataframe3, query_keywords, keys_list[
					no_of_keys_for_shc:no_of_keys_for_shc + no_of_keys_for_site_specific_search], cse_id, output_dir)

	# result_dataframe4 = pd.read_csv(
	# 	"/Users/tejasvibelsare/Desktop/all_contraception/Output 2020-07-14 18:58:27/keywords_matched_webpages_on_SHC.csv")

	# store_data_from_webpages.save_webpage_content(result_dataframe4, output_dir)

	### Get data from the urls found under shc
	# result_dataframe5 = get_data_from_url_with_pdf.retrieve_content_from_urls(result_dataframe4, keyword_list, output_dir)
	result_dataframe5 = webpage_crawling.retrieve_content_from_urls(result_dataframe4, keyword_list,
																	output_dir, driver_path)

	####find relevant content from retrieved website data
	# result_dataframe5 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/manual_error_navigation/Output 2020-09-10 15:44:34/get_data_from_url_output_without_pdf_links.csv")
	result_dataframe6, keyword_list = filter_relevant_data.find_relevant_content(result_dataframe5, keyword_list, output_dir)

	### calculate overall reading level of content retrieved from the urls
	result_dataframe7 = reading_level.get_reading_level(result_dataframe6, output_dir)

	# result_dataframe7 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/superset/Output 2020-09-18 01:27:36/Reading_level_of_content_without_pdf.csv")

	#### Quantity metric
	result_dataframe8 = quantity_metrics.metric_calculation(result_dataframe7, keyword_list, output_dir)

	# result_dataframe8.to_csv(output_dir + '/final_compiled_output.csv')  ## storing output


	'''
	result_dataframe6 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/manual_error_navigation"
									"/Output 2020-08-10 15:50:29/get_relevant_data_from_collected_data_without_pdf_links.csv")

	result_dataframe3 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/manual_error_navigation"
									"/Output 2020-08-10 15:50:29/University_SHC.csv")

	result_dataframe8 = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/manual_error_navigation"
									"/Output 2020-08-10 15:50:29/Keywords_count_for_universities.csv")
	'''

	result_dataframe9 = metric_calculation.calculate_metrics(result_dataframe6, output_dir, ideal_doc)


	final_result_df= combine_results.combine_all_results_together(result_dataframe8, result_dataframe9, result_dataframe3, output_dir)

	final_result_df.to_csv(output_dir + '/final_output.csv')

	end_time = datetime.datetime.now()

	time_required_for_SHC = uni_shc_time - start_time
	time_required = end_time - start_time
	print("Total time required to run the program is : ", time_required.seconds / 60)
	time_file = output_dir + "/required_time"

	f = open(time_file, "a")
	f.write("Start time: " + str(start_time) + "\nEnd time: " + str(end_time) +
			"\nTotal required time: " + str(round(time_required.seconds / 60, 3)) + " minutes" + "\nTime required to find uni shc: "
			+ str(round(time_required_for_SHC.seconds/60, 3)) + " minutes")
	f.close()


if __name__ == "__main__":
	import sys

	print(sys.argv)

main()
