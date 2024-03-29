"""
Calculates number of keywords occurred in the SHC pages of given university
Input - University name along with relevant content
Output - Getting prevalence metric as per keywords provided
"""

import pandas as pd


# Getting keyword count for given content
def metric_count(found_per_stem_dictionary, phrase_stem_dictionary, keywords):
	count_dict = {}
	print("   - Keywords quantity")

	# For every keyword given
	for each_keyword in keywords:
		matched_stem = ''
		for stem in phrase_stem_dictionary:
			for phrase in phrase_stem_dictionary[stem]:
				joined_phrase = ' '.join(phrase)
				if joined_phrase == each_keyword:
					matched_stem = stem
					break
			else:
				continue
			break
		count_dict[each_keyword] = len(found_per_stem_dictionary[matched_stem])
	return count_dict


def get_prevalence(metric_dataframe):

	print("   - Prevalence")
	return metric_dataframe.sum(axis=1)


def get_coverage(metric_dataframe, input_keyword_count):

	print("   - Coverage")
	present_keyword_count = metric_dataframe.astype(bool).sum(axis=1).values
	coverage_percent = '{0:.2f}'.format(present_keyword_count[0] / input_keyword_count * 100)
	return coverage_percent


# Calculating count of keywords for prevalence metric
def metric_calculation(input_dataframe, keywords, output_dir, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary):
	header = ['University name', 'University SHC URL', 'Count of SHC webpages matching keywords',
			  'Keywords matched webpages on SHC', 'Total word count on all pages', 'Num of sentences', 'Num of syllables',
			  'Num of words', 'Reading ease', 'Grade level', 'Prevalence_metric', 'Percent_coverage']

	# Headers are created based on the dictionary created during the filtering step
	list_of_keyword_headers = []
	for i in range(len(keywords)):
		matched_stem = ''
		for stem in phrase_stem_dictionary:
			for phrase in phrase_stem_dictionary[stem]:
				joined_phrase = ' '.join(phrase)
				if joined_phrase == keywords[i]:
					matched_stem = stem
					break
			else:
				continue
			break
		phrases_matching_stem = set()
		for d in list_of_stem_found_phrase_dictionary:
			for item in d[matched_stem]:
				phrases_matching_stem.add(item)
		if not phrases_matching_stem:
			list_of_keyword_headers.append(keywords[i])
		else:
			list_of_keyword_headers.append(keywords[i] + "(" + ','.join(phrases_matching_stem) + ")")
	
	input_keyword_count = len(list_of_keyword_headers)
	header.extend(list_of_keyword_headers)
	output_dataframe = pd.DataFrame(columns=header)

	# For every university's relevant content
	for index, row in input_dataframe.iterrows():
		
		university = row["University name"]
		contents = row["Relevant content on all pages"]
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']
		no_of_sentences = row['Num of sentences']
		no_of_syllables = row['Num of syllables']
		no_of_words = row['Num of words']
		reading_ease = row['Reading ease']
		grade_level = row['Grade level']
		total_words = row['Total word count on all pages']

		print("- ", university)

		try:
			if not contents:
				print("   - No content found!")
			# Check if content is available
			else:
				# Getting dictionary of keywords with count of keywords
				metric_array = metric_count(list_of_found_per_stem_dictionary[index], phrase_stem_dictionary, keywords)
				# Replacing dict keys to reflect headers
				index = 0
				modified_metric_array = {}
				for key in metric_array:
					modified_metric_array[list_of_keyword_headers[index]] = metric_array[key]
					index += 1
				metric_dataframe = pd.DataFrame([modified_metric_array])

				# Calculating prevalence metric
				prevalence = get_prevalence(metric_dataframe)

				# Calculating coverage metric
				coverage = get_coverage(metric_dataframe, input_keyword_count)

				metric_dataframe["Percent_coverage"] = coverage
				metric_dataframe["Prevalence_metric"] = prevalence

				uni_dict = {
					'University name': university,
					'University SHC URL': shc,
					'Count of SHC webpages matching keywords': no_of_links,
					'Keywords matched webpages on SHC': link_data,
					'Total word count on all pages': total_words,
					'Num of sentences': no_of_sentences,
					'Num of syllables': no_of_syllables,
					'Num of words': no_of_words,
					'Reading ease': reading_ease,
					'Grade level': grade_level
				}
				# Converting dictionary into dataframe
				uni_dataframe = pd.DataFrame([uni_dict])
				# Concatenating university names with respective counts
				result = pd.concat([uni_dataframe, metric_dataframe], axis=1)
				result = result[output_dataframe.columns]
				# Appending current dataframe to output dataframe
				output_dataframe = pd.concat([output_dataframe, result], sort=False)

		except Exception as e:
			print(e)
			output_dataframe = pd.concat([output_dataframe, pd.DataFrame.from_dict(
				{
					'University name': university,
					'University SHC URL': shc,
					'Count of SHC webpages matching keywords': no_of_links,
					'Keywords matched webpages on SHC': link_data,
					'Total word count on all pages': total_words,
					'Num of sentences': no_of_sentences,
					'Num of syllables': no_of_syllables,
					'Num of words': no_of_words,
					'Reading ease': reading_ease,
					'Grade level': grade_level

				}, orient='index').transpose()], ignore_index=True)
		
	output_dataframe.to_csv(output_dir + '/Keywords_count_for_universities.csv')

	return output_dataframe
