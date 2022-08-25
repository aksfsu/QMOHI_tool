"""
Find data relevant to the keywords from the data retrieved from program retrieved URLs
Input - all data retrieved from the URLs
Output - data relevant to the keywords
"""
from nltk.text import Text
from nltk import tokenize
from nltk.stem.snowball import SnowballStemmer
import nltk
import nltk.corpus
import pandas as pd
import os
import re
from gensim.parsing.preprocessing import strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation

nltk.download('gutenberg')  # Can be run only once in the beginning


class RelevantContent:
	def __init__(self, uni_name, relevant_content_file):
		self.uni_name = uni_name
		self.content = Text(nltk.corpus.gutenberg.words(relevant_content_file))

	def relevant_content_words(self, keywords):
		# Concordance referred from https://simplypython.wordpress.com/2014/03/14/saving-output-of-nltk-text-concordance/
		tokens = [remove_circumflex_a(token) for token in self.content.tokens if remove_circumflex_a(token)]

		# Stemming tokens before finding relevant content. Assumption: keywords have/will be been stemmed
		stemmer = SnowballStemmer("english")
		# token_stem_dictionary is structured as such: {'stem': [(index, 'non-stemmed-token'),(index, 'non-stemmed-token'),...],...}
		token_stem_dictionary = {}
		for i in range(len(tokens)):
			stemmed_token = stemmer.stem(tokens[i])
			if stemmed_token in token_stem_dictionary:
				token_stem_dictionary[stemmed_token].append(tuple([i, tokens[i]]))
			else:
				token_stem_dictionary[stemmed_token] = [(i, tokens[i])]
		stemmed_tokens = [stemmer.stem(token) for token in tokens]

		# Stemming the phrase list for filtering step only
		# phrase_stem_dictionary is structured as such: {'stem': ['non-stemmed-token', 'non-stemmed-token',...],...}
		phrase_stem_dictionary = {}
		for phrase in keywords:
			phrase_list = phrase.split(' ')
			stemmed_phrase_list = []
			for i in range(len(phrase_list)):
				stemmed_phrase_list.append(stemmer.stem(phrase_list[i]))
			stemmed_phrase = ' '.join(stemmed_phrase_list)
			if stemmed_phrase in phrase_stem_dictionary:
				phrase_stem_dictionary[stemmed_phrase].append(phrase_list)
			else:
				phrase_stem_dictionary[stemmed_phrase] = [phrase_list]

		# found_per_stem_dictionary is structured as such: {'stem': [index1, index2, index3]}
		found_per_stem_dictionary = {}

		# Keeps track of the keyword index in the content and retrieve the surrounding words
		c = nltk.ConcordanceIndex(stemmed_tokens, key=lambda s: s.lower())
		for phrase in phrase_stem_dictionary:
			stemmed_phrase_list = phrase.split(' ')
			# Find the offset for each token in the phrase
			offsets = [c.offsets(x) for x in stemmed_phrase_list]
			temp_list = offsets[0][:]
			found_per_stem_dictionary[phrase] = offsets[0][:]
			for i in range(len(temp_list)):
				for j in range(1, len(offsets)):
					if temp_list[i]+j not in offsets[j]:
						if temp_list[i] in found_per_stem_dictionary[phrase]:
							found_per_stem_dictionary[phrase].remove(temp_list[i])

			# stem_found_phrase_dictionary is a dictionary structured as such {'stem': ['unstemmed matching phrase1', 'unstemmed matching phrase1']}
			stem_found_phrase_dictionary = {}
			for stem in found_per_stem_dictionary:
				stem_list = stem.split()
				phrases_list = []
				for index in found_per_stem_dictionary[stem]:
					phrase_list = []
					for i in range(len(stem_list)):
						phrase_list.append(tokens[index + i])
					phrase = ' '.join(phrase_list)
					phrases_list.append(phrase)
				stem_found_phrase_dictionary[stem] = phrases_list
		return found_per_stem_dictionary, phrase_stem_dictionary, stem_found_phrase_dictionary


# Removing unwanted characters from data
def remove_circumflex_a(input_str):
	input_str = input_str.replace('Â', '')
	output_str = input_str.replace('â', '')
	return output_str


# Remove tags and unwanted data here
def get_topical_contents(input_str, keywords):
	complete_data_series = pd.Series(input_str.split("\n"))
	topical_indices = set()

	for index, row in complete_data_series.iteritems():
		# Drop sentences that do not contain any keyword
		if not all(x not in row.lower() for x in keywords):
			for i in range(min(0, index - 5), max(len(complete_data_series), index + 5)):
				topical_indices.add(i)

	for index, row in complete_data_series.iteritems():
		if index not in topical_indices:
			complete_data_series.drop(labels=[index], inplace=True)
		else:
			# Remove punctuation
			row = strip_punctuation(row)
			# Remove non-alphanumeric characters
			row = strip_non_alphanum(row)
			# Remove numeric characters
			row = strip_numeric(row)
			# Remove redundant white spaces
			row = strip_multiple_whitespaces(row)
			complete_data_series[index] = row

	# Join final data with new line character
	cleaned_content = '\n'.join(complete_data_series)
	cleaned_content = re.sub(r"\s*\.+\s*\.*", ". ", cleaned_content, flags=re.MULTILINE)
	return cleaned_content


def add_space_in_keywords(keywords):
	non_alphabets_list = ['_', '-', ':']
	for every_item in non_alphabets_list:
		replacing_item = " " + every_item + " "
		keywords = [sub.replace(every_item, replacing_item) for sub in keywords]
	return keywords


# Find relevant content from the data provided on the basis of keywords
def find_relevant_content(input_dataframe, keywords, output_dir):
	header = ['University name', 'University SHC URL', 'Count of SHC webpages matching keywords',
			  'Keywords matched webpages on SHC', 'Total word count on all pages', 'Relevant content on all pages']
	output_dataframe = pd.DataFrame(columns=header)
	spaced_keywords = add_space_in_keywords(keywords)
	phrase_stem_dictionary = []
	list_of_found_per_stem_dictionary = []
	list_of_stem_found_phrase_dictionary = []
	# For every university in the dataframe
	for index, row in input_dataframe.iterrows():
		found_per_stem_dictionary = []
		stem_found_phrase_dictionary = []
		relevant_content = []
		university = row['University name']
		content = row['Content on all retrieved webpages']
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']
		total_words = row['Total word count on all pages']
		print("- ", university)

		# Try writing content in the text file
		try:
			relevant_content_file = output_dir + "/relevant_content.txt"
			content = get_topical_contents(content, keywords)
			out_file = open(relevant_content_file, 'w')
			out_file.write(content)
			out_file.close()
			# Creating object per university
			uni_object = RelevantContent(university, relevant_content_file)
			# Words_content here is list of lists
			found_per_stem_dictionary, phrase_stem_dictionary, stem_found_phrase_dictionary = uni_object.relevant_content_words(spaced_keywords)
			# Deleting relevant_file.txt
			os.remove(relevant_content_file)

		except Exception as e:
			print(e)

		if content:
			list_of_found_per_stem_dictionary.append(found_per_stem_dictionary)
			list_of_stem_found_phrase_dictionary.append(stem_found_phrase_dictionary)
			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of SHC webpages matching keywords': no_of_links,
														'Keywords matched webpages on SHC': link_data,
														'Relevant content on all pages': content,
														'Total word count on all pages': total_words
														}, ignore_index=True)

	# Storing output dataframe
	output_dataframe.to_csv(output_dir + '/get_relevant_data_from_collected_data.csv')

	# Returning output dataframe and space added keywords for metric calculation
	return output_dataframe, spaced_keywords, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary
