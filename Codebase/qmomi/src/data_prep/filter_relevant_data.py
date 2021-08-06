"""
Find data relevant to the keywords from the data retrieved from program retrieved URLs
Input - all data retrieved from the URLs
Output - data relevant to the keywords
"""
from nltk.text import Text
from nltk import tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import nltk
import nltk.corpus
import pandas as pd
import os
import time
import datetime

nltk.download('gutenberg')  # Can be run only once in the beginning


class RelevantContent:
	# Number of words in the margin
	left_margin = 90
	right_margin = 90

	def __init__(self, uni_name, relevant_content_file):
		self.uni_name = uni_name
		self.content = Text(nltk.corpus.gutenberg.words(relevant_content_file))

	def relevant_content_words(self, keywords):
		# Concordance referred from https://simplypython.wordpress.com/2014/03/14/saving-output-of-nltk-text-concordance/
		list_of_sentences = []
		tokens = []
		for each_token in self.content.tokens:
			tokens.append(remove_circumflex_a(each_token))

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

		print("Phrase Stem Dictionary: ")
		print(phrase_stem_dictionary)

		# found_per_stem_dictionary is structured as such: {'stem': [index1, index2, index3]}
		found_per_stem_dictionary = {}

		# Keeps track of the keyword index in the content and retrieve the surrounding words
		c = nltk.ConcordanceIndex(stemmed_tokens, key=lambda s: s.lower())
		for phrase in phrase_stem_dictionary:
			stemmed_phrase_list = phrase.split(' ')
			# stemmed_phrase_list = list(phrase)
			# Find the offset for each token in the phrase
			offsets = [c.offsets(x) for x in stemmed_phrase_list]
			offsets_norm = []
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
			# For each token in the phrase list, find the offsets tokenize and rebase them to the start of the phrase
			for i in range(len(stemmed_phrase_list)):
				offsets_norm.append([x - i for x in offsets[i]])

			# Storing content in the set so that, overlapping/ duplicate content can be removed
			intersects = set(offsets_norm[0]).intersection(*offsets_norm[1:])

			# Getting text as per left and right margin provided
			concordance_txt = ([self.content.tokens[
								list(
									map(lambda x: x - self.left_margin if (x - self.left_margin) > 0 else 0, [offset]))[
									0]:offset + len(
									stemmed_phrase_list) + self.right_margin]
								for offset in intersects])

			# Combining all lists together as single content
			outputs = [''.join([x + ' ' for x in con_sub]) for con_sub in concordance_txt]
			# Ignore if no content was retrieved
			if outputs:
				list_of_sentences.append(outputs)
			# print("list of sentences: ")
			# print(list_of_sentences)
		return list_of_sentences, found_per_stem_dictionary, phrase_stem_dictionary, stem_found_phrase_dictionary


# Converting words into sentences from left and right margin
def convert_words_sentences(words_content):
	sentences_array = tokenize.sent_tokenize(words_content)
	# remove duplicate sentences from data
	seen = set()
	unique_sentences = []
	for sentence in sentences_array:
		if sentence not in seen:
			seen.add(sentence)
			unique_sentences.append(sentence)

	return unique_sentences


# Removing unwanted characters from data
def remove_circumflex_a(input_str):
	input_str = input_str.replace('Â', '')
	output_str = input_str.replace('â', '')

	return output_str


# Join array together with new line character
def join_array(sentences_array):
	complete_content = "\n".join(sentences_array)

	return complete_content


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
	keywords = add_space_in_keywords(keywords)
	list_of_found_per_stem_dictionary = []
	list_of_stem_found_phrase_dictionary = []
	# For every university in the dataframe
	for index, row in input_dataframe.iterrows():
		timestamp = time.time()
		date = datetime.datetime.fromtimestamp(timestamp)
		print("Start:", date.strftime('%H:%M:%S.%f'))

		final_relevant_content = []
		seen_content = set()
		unique_content = []
		university = row['University name']
		content = row['Content on all retrieved webpages']
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		links = row['Keywords matched webpages on SHC']
		total_words = row['Total word count on all pages']
		print("- ", university)

		if content != "No content":
			# Try writing content in the text file
			try:
				relevant_content_file = output_dir + "/relevant_content.txt"
				out_file = open(relevant_content_file, 'w')
				out_file.write(content)
				out_file.close()
				# Creating object per university
				uni_object = RelevantContent(university, relevant_content_file)
				# Words_content here is list of lists
				words_content_list, found_per_stem_dictionary, phrase_stem_dictionary, stem_found_phrase_dictionary = uni_object.relevant_content_words(keywords)
				list_of_found_per_stem_dictionary.append(found_per_stem_dictionary)
				list_of_stem_found_phrase_dictionary.append(stem_found_phrase_dictionary)
				# Joining lists together with full stop
				for words_content in words_content_list:

					joined_words_content = ". ".join(words_content)
					sentences_array = convert_words_sentences(joined_words_content)

					# Checking for duplicate content
					for each_sentence in sentences_array:
						if each_sentence not in seen_content:
							seen_content.add(each_sentence)
							unique_content.append(each_sentence)

					sentences_content = join_array(unique_content)
					# Final content after removing duplicate sentences
					final_relevant_content.append(sentences_content)

				# Deleting relevant_file.txt
				os.remove(relevant_content_file)

			except Exception as e:
				print(e)

			# All the content on all pages for 1 university
			joined_final_relevant_content = "\n".join(unique_content)

			# Removing unwanted characters (circumflex a)
			removed_unicode = remove_circumflex_a(joined_final_relevant_content)
			# Check if final content is only space
			if removed_unicode.isspace() or not removed_unicode:
				# If data is white space
				pass
			# Writing to dataframe
			else:
				output_dataframe = output_dataframe.append({'University name': university,
															'University SHC URL': shc,
															'Count of SHC webpages matching keywords': no_of_links,
															'Keywords matched webpages on SHC': links,
															'Relevant content on all pages': removed_unicode,
															'Total word count on all pages': total_words
															}, ignore_index=True)
		else:
			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of SHC webpages matching keywords': no_of_links,
														'Keywords matched webpages on SHC': links,
														'Relevant content on all pages': content,
														# Content contains "No content here!
														'Total word count on all pages': total_words
														}, ignore_index=True)
		timestamp = time.time()
		date = datetime.datetime.fromtimestamp(timestamp)
		print("End:", date.strftime('%H:%M:%S.%f'))

	# Storing output dataframe
	output_dataframe.to_csv(output_dir + '/get_relevant_data_from_collected_data_without_pdf_links.csv')

	# Returning output dataframe and space added keywords for metric calculation
	return output_dataframe, keywords, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary
