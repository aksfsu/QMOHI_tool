"""
Calculates the reading ease score and grade level score of the content
Input - data of which reading level has to be calculated
Output - reading ease score and grade level score of the data
"""
from spacy.lang.en import English
import pandas as pd
import re
from gensim.parsing.preprocessing import strip_numeric

class Readability:

	def __init__(self, sentences):
		self.sentences = [re.sub(r"[^A-Za-z0-9 ]+", "", sentence) for sentence in sentences]
		self.n_sentences = len(sentences)
		self.n_words = self.word_count()
		self.n_syllables = self.syllable_count()
		print('	n_words =', self.n_words)
		print('	n_sentences = ', self.n_sentences)
		print('	n_syllables = ', self.n_syllables)

	def get_num_of_sentences(self):
		return self.n_sentences

	def get_num_of_words(self):
		return self.n_words

	def get_num_of_syllables(self):
		return self.n_syllables

	# Calculate total number of syllables in all the sentences
	def syllable_count(self):
		n_syllables = 0
		vowels = "aeiouy"

		# For every word in the content
		for sentence in self.sentences:
			# Remove numeric tokens
			sentence = strip_numeric(sentence)

			for word in sentence.split():
				word = word.lower()
				syllable_count = 0

				if word[0] in vowels:
					syllable_count += 1

				for index in range(1, len(word)):
					if word[index] in vowels and word[index - 1] not in vowels:
						syllable_count += 1

				if word.endswith("e"):
					syllable_count -= 1
				
				if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
					syllable_count += 1

				if syllable_count == 0:
					syllable_count += 1

				n_syllables += syllable_count

		return n_syllables

	# Calculating number of sentences with Spacy
	def sentence_count(self):
		nlp = English()
		# sentencizer = nlp.create_pipe("sentencizer")
		nlp.add_pipe("sentencizer")

		n_sentences = 0
		for sentence in self.sentences:
			doc = nlp(sentence)
			n_sentences += len(list(doc.sents))

		return n_sentences

	# Calculating number of words with Spacy
	def word_count(self):
		return sum(len(sentence.split()) for sentence in self.sentences)

	# Calculating reading ease score as per formula
	def get_reading_ease_score(self):
		# Flesch reading ease formula
		score = 206.835 - 1.015 * (self.n_words / self.n_sentences) - 84.6 * (self.n_syllables / self.n_words)
		score = round(score, 2)
		return score

	# Calculating grade level score as per formula
	def get_grade_level_score(self):
		# Flesch–Kincaid grade level formula
		score = 0.39 * (self.n_words / self.n_sentences) + 11.8 * (self.n_syllables / self.n_words) - 15.59
		score = round(score, 2)
		return score


# Calculating reading level of the given content
def get_reading_level(input_dataframe, output_dir):
	header = ['University name', 'University SHC URL', 'Relevant content on all pages',
			  'Count of SHC webpages matching keywords', 'Keywords matched webpages on SHC',
			  'Total word count on all pages', 'Num of sentences', 'Num of syllables', 'Num of words', 'Reading ease',
			  'Grade level']
	output_dataframe = pd.DataFrame(columns=header)

	# For every university
	for index, row in input_dataframe.iterrows():

		university = row["University name"]
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']
		contents = row["Relevant content on all pages"]
		total_words = row["Total word count on all pages"]

		print("- ", university)

		try:
			# If the content has only spaces
			if not contents:
				print("   - Relevant information contains only whitespace!")

				output_dataframe = output_dataframe.append(
					{
						'University name': university,
						'University SHC URL': shc,
						'Count of SHC webpages matching keywords': no_of_links,
						'Keywords matched webpages on SHC': link_data,
						'Total word count on all pages': total_words,
						'Num of sentences': 0,
						'Num of syllables': 0,
						'Num of words': 0,
						'Reading ease': 0,
						'Grade level': 0
					}, ignore_index=True)

			# If content is present
			else:
				readability = Readability(contents)

				# Calculate reading ease
				reading_ease = readability.get_reading_ease_score()

				# Calculate grade level
				grade_level = readability.get_grade_level_score()

				# Append current dataframe to overall result
				output_dataframe = output_dataframe.append(
					{
						'University name': university,
						'University SHC URL': shc,
						'Relevant content on all pages': contents,
						'Count of SHC webpages matching keywords': no_of_links,
						'Keywords matched webpages on SHC': link_data,
						'Total word count on all pages': total_words,
						'Num of sentences': readability.get_num_of_sentences(),
						'Num of syllables': readability.get_num_of_syllables(),
						'Num of words': readability.get_num_of_words(),
						'Reading ease': reading_ease,
						'Grade level': grade_level
					}, ignore_index=True)
		# If there is some error in the reading content
		except Exception as e:
			print(e)
			output_dataframe = output_dataframe.append(
				{
					'University name': university,
					'University SHC URL': shc,
					'Relevant content on all pages': contents,
					'Count of SHC webpages matching keywords': no_of_links,
					'Keywords matched webpages on SHC': link_data,
					'Total word count on all pages': total_words,
					'Reading ease': "Error in reading content!",
					'Grade level': "Error in reading content!"
				}, ignore_index=True)

	# Storing results
	output_dataframe.to_csv(output_dir + '/Reading_level_of_content.csv')

	return output_dataframe
