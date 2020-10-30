"""
Calculates number of keywords occurred in the SHC pages of given university
Input - University name along with relevant content
Output - Getting prevalence metric as per keywords provided
"""

import pandas as pd
import re


class QuantityMetrics:

	def __init__(self, content):
		self.content = content

	# Getting keyword count for given content
	def metric_count(self, keywords):
		count_dict = {}

		# For every keyword given
		for each_keyword in keywords:
			count = len(re.findall(each_keyword, self.content, flags=re.IGNORECASE))
			count_dict[each_keyword] = count

		return count_dict


def get_prevalence(metric_dataframe):

	return metric_dataframe.sum(axis=1)


def get_coverage(metric_dataframe, input_keyword_count):

	present_keyword_count = metric_dataframe.astype(bool).sum(axis=1).values
	coverage_percent = '{0:.2f}'.format(present_keyword_count[0] / input_keyword_count * 100)

	return coverage_percent


# Calculating count of keywords for prevalence metric
def metric_calculation(input_dataframe, keywords, output_dir):
	header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC',
			  'Keywords matched webpages on SHC', 'Total word count on all pages', 'Num of sentences', 'Num of syllables',
			  'Num of words', 'Reading ease', 'Grade level', 'Prevalence_metric', 'Percent_coverage']

	input_keyword_count = len(keywords)
	# Extending header as per keywords provided
	header.extend(keywords)
	print(f"----> {header}------>")
	output_dataframe = pd.DataFrame(columns=header)

	# For every university's relevant content
	for index, row in input_dataframe.iterrows():

		university = row["University name"]
		content = row["Relevant content on all pages"]
		shc = row['University SHC URL']
		no_of_links = row['Count of keywords matching webpages on SHC']
		links = row['Keywords matched webpages on SHC']
		no_of_sentences = row['Num of sentences']
		no_of_syllables = row['Num of syllables']
		no_of_words = row['Num of words']
		reading_ease = row['Reading ease']
		grade_level = row['Grade level']
		total_words = row['Total word count on all pages']

		print("\n", university)

		try:
			if content.isspace() or content == "No content":
				print("No content")
			# check if content is available
			else:
				content_obj = QuantityMetrics(content)
				# Getting dictionary of keywords with count of keywords
				metric_array = content_obj.metric_count(keywords)
				print(metric_array.items())
				# Converting dict into dataframe
				metric_dataframe = pd.DataFrame([metric_array])

				# Calculating prevalence metric
				prevalence = get_prevalence(metric_dataframe)

				# Calculating coverage metric
				coverage = get_coverage(metric_dataframe, input_keyword_count)

				metric_dataframe["Percent_coverage"] = coverage
				metric_dataframe["Prevalence_metric"] = prevalence

				uni_dict = {
					'University name': university,
					'University SHC URL': shc,
					'Count of keywords matching webpages on SHC': no_of_links,
					'Keywords matched webpages on SHC': links,
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
				output_dataframe = output_dataframe.append(result)

		except Exception as e:
			print(e)
			output_dataframe = output_dataframe.append(
				{
					'University name': university,
					'University SHC URL': shc,
					'Count of keywords matching webpages on SHC': no_of_links,
					'Keywords matched webpages on SHC': links,
					'Total word count on all pages': total_words,
					'Num of sentences': no_of_sentences,
					'Num of syllables': no_of_syllables,
					'Num of words': no_of_words,
					'Reading ease': reading_ease,
					'Grade level': grade_level

				}, ignore_index=True)
	# Storing output
	output_dataframe.to_csv(output_dir + '/Keywords_count_for_universities.csv')

	return output_dataframe
