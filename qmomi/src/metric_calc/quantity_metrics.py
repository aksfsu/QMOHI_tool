'''
Calculates number of keywords occurred in the SHC pages of given university
input - University name along with relevant content
output - Getting prevalence metric as per keywords provided
'''

import pandas as pd
import re


class quantity_metrics:

	def __init__(self, content):
		self.content = content

	### getting keyword count for given content
	def metric_count(self, keywords):
		count_dict = {}

		### for every keyword given
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


### calculating count of keywords for prevalence metric
def metric_calculation(input_dataframe, keywords, output_dir):
	# header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC', 'Keywords matched webpages on SHC']
	header = ['University name', 'University SHC URL', 'Count of keywords matching webpages on SHC',
			  'Keywords matched webpages on SHC',
			  'Total word count on all pages', 'Num of sentences', 'Num of syllables', 'Num of words', 'Reading ease',
			  'Grade level', 'Prevalence_metric', 'Percent_coverage']

	input_keyword_count = len(keywords)

	header.extend(keywords)  ### extending header as per keywords provided
	print(f"----> {header}------>")
	output_dataframe = pd.DataFrame(columns=header)

	##for every university's relevant content
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

			else:  ### check if content is available

				content_obj = quantity_metrics(content)

				metric_array = content_obj.metric_count(
					keywords)  ## getting dictionary of keywords with count of keywords
				print(metric_array.items())

				metric_dataframe = pd.DataFrame([metric_array])  ##converting dict into dataframe

				# Calculating prevalence metric
				prevalence = get_prevalence(metric_dataframe)

				coverage = get_coverage(metric_dataframe, input_keyword_count)

				metric_dataframe["Percent_coverage"] = coverage
				metric_dataframe["Prevalence_metric"] = prevalence
				# metric_dataframe["Prevalence_metric"] = metric_dataframe.sum(axis=1)

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

				uni_dataframe = pd.DataFrame([uni_dict])  ## converting dictionary into dataframe

				result = pd.concat([uni_dataframe, metric_dataframe],
								   axis=1)  ## concatenating university names with respective counts

				print(f"----> result------> {result}")

				result = result[output_dataframe.columns]

				output_dataframe = output_dataframe.append(result)  ## appending current dataframe to output dataframe


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

	output_dataframe.to_csv(output_dir + '/Keywords_count_for_universities.csv')  ## storing output

	return output_dataframe


'''
# keywords = ['IUD', 'Progesterone IUD', 'Progestin', 'Hormonal IUD', 'Mirena', 'Skyla', 'Kyleena', 'Liletta',
# 		   'Copper IUD', 'Non-Hormonal IUD', 'Nonhormonal IUD', 'Paragard', 'Contraceptive implant',
# 		   'Nexplanon', 'Contraceptive injection', 'Control shot', 'Depo-Provera', 'Depo', 'Condom',
# 		   'Condoms', 'Emergency contraception', 'Emergency contraceptives', 'Morning after pill',
# 		   'Plan B', 'Levonorgestrel', 'Ella', 'Ulipristal acetate', 'Contraceptive pill', 'Control pill',
# 		   'Diaphragm', 'Spermicide', 'Contraceptive patch', 'Control patch', 'Vaginal ring', 'Control ring',
# 		   'Contraceptive ring', 'Cervical cap', 'Birth control']

keywords =['Birth Control', 'IUD',
'Progesterone IUD',
'Progestin',
'Hormonal IUD',
'Mirena',
'Skyla',
'Kyleena',
'Liletta',
'Copper IUD',
'Non-Hormonal IUD',
'Nonhormonal IUD',
'Paragard',
'Contraceptive implant',
'Nexplanon',
'Contraceptive injection',
'Control shot',
'Depo-Provera',
'Depo',
'emergency contraception',
'emergency contraceptives',
'morning after pill',
'Plan B',
'levonorgestrel',
'ella',
'ulipristal acetate',
'contraceptive pill',
'control pill',
'diaphragm',
'spermicide',
'contraceptive patch',
'control patch',
'vaginal ring',
'control ring',
'contraceptive ring',
'cervical cap',
'pap smear',
'pap smears',
'papsmear',
'papsmears',
'pap test',
'pap tests',
'Condom',
'Condoms']


output_dir = "/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/superset"
input_dataframe = pd.read_csv("/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/new_results/superset/Output 2020-09-18 01:27:36/Reading_level_of_content_without_pdf.csv")

metric_calculation(input_dataframe, keywords, output_dir)
'''