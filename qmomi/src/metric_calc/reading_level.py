'''
Calculates the reading ease score and grade level score of the content
Input - data of which reading level has to be calculated
Output - reading ease score and grade level score of the data
'''

from spacy.lang.en import English
import pandas as pd


class reading_level:

	def __init__(self, content):
		self.content = content

	## calculate syllables in the content
	def syllable_count(self):

		n_syllables = 0

		## for every word in the content
		for word in self.content.split():

			word = word.lower()
			count = 0
			vowels = "aeiouy"

			if word[0] in vowels:
				count += 1

			for index in range(1, len(word)):
				if word[index] in vowels and word[index - 1] not in vowels:
					count += 1

			## not considering "e" if its at the end of the word
			if word.endswith("e"):
				count -= 1

			##considering minimum 1 syllable
			if count == 0:
				count += 1

			n_syllables = n_syllables + count  ## syllables count for complete content

		print("Total syllables: %d" % n_syllables)

		return n_syllables

	### calculating number of sentences with Spacy
	def sentence_count(self):
		nlp = English()
		sentencizer = nlp.create_pipe("sentencizer")
		nlp.add_pipe(sentencizer)

		doc = nlp(self.content)
		print("Spacy sentence count", len(list(doc.sents)))
		n_sentences = len(list(doc.sents))

		return n_sentences

	## calculating number of words with Spacy
	def word_count(self):
		nlp = English()
		doc = nlp(self.content)

		words = [token.text for token in doc]
		n_words = len(words)
		print("Spacy word count", len(words))

		return n_words

	##calculating reading ease score as per formula
	def get_reading_ease_score(self, n_words, n_sentences, n_syllables):
		# Flesch reading ease formula
		score = 206.835 - 1.015 * (n_words / n_sentences) - 84.6 * (n_syllables / n_words)
		score = round(score, 2)
		return score

	##calculating grade level score as per formula
	def get_grade_level_score(self, n_words, n_sentences, n_syllables):
		# Flesch–Kincaid grade level formula
		score = 0.39 * (n_words / n_sentences) + 11.8 * (n_syllables / n_words) - 15.59
		score = round(score, 2)
		return score


### Calculating reading level of the given content
def get_reading_level(input_dataframe, output_dir):
	header = ['University name', 'University SHC URL', 'Relevant content on all pages',
			  'Count of keywords matching webpages on SHC', 'Keywords matched webpages on SHC',
			  'Total word count on all pages', 'Num of sentences', 'Num of syllables', 'Num of words', 'Reading ease',
			  'Grade level']
	output_dataframe = pd.DataFrame(columns=header)

	## for every university
	for index, row in input_dataframe.iterrows():

		university = row["University name"]
		shc = row['University SHC URL']
		no_of_links = row['Count of keywords matching webpages on SHC']
		links = row['Keywords matched webpages on SHC']
		content = row["Relevant content on all pages"]
		total_words = row["Total word count on all pages"]

		print("\n", university)

		try:
			if content.isspace():  ### if the content has only spaces
				print("Content contains only whitespace!")

				output_dataframe = output_dataframe.append(
					{
						'University name': university,
						'University SHC URL': shc,
						'Count of keywords matching webpages on SHC': no_of_links,
						'Keywords matched webpages on SHC': links,
						'Total word count on all pages': total_words,
						'Num of sentences': 0,
						'Num of syllables': 0,
						'Num of words': 0,
						'Reading ease': 0,
						'Grade level': 0
					}, ignore_index=True)

			elif content == "No content":
				#### if no links found with LARC keywords under SHC

				output_dataframe = output_dataframe.append(
					{
						'University name': university,
						'University SHC URL': shc,
						'Count of keywords matching webpages on SHC': no_of_links,
						'Keywords matched webpages on SHC': links,
						'Total word count on all pages': total_words,
						'Num of sentences': "NA",
						'Num of syllables': "NA",
						'Num of words': "NA",
						'Reading ease': "NA",
						'Grade level': "NA"
					}, ignore_index=True)

			else:  # content != "No content":               ### if content is present

				content_obj = reading_level(content)

				# calculate all the numbers required for the formula
				n_sentences = content_obj.sentence_count()
				n_words = content_obj.word_count()
				n_syllables = content_obj.syllable_count()

				## calculate reading ease
				reading_ease = content_obj.get_reading_ease_score(n_words, n_sentences, n_syllables)
				print("reading ease score: " + "{:.2f}".format(reading_ease))

				###calculate grade level
				grade_level = content_obj.get_grade_level_score(n_words, n_sentences, n_syllables)
				print("grade level: " + "{:.2f}".format(grade_level))

				'''
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
				
				'''

				output_dataframe = output_dataframe.append(  ### append current dataframe to overall result
					{
						'University name': university,
						'University SHC URL': shc,
						'Relevant content on all pages': content,
						'Count of keywords matching webpages on SHC': no_of_links,
						'Keywords matched webpages on SHC': links,
						'Total word count on all pages': total_words,
						'Num of sentences': n_sentences,
						'Num of syllables': n_syllables,
						'Num of words': n_words,
						'Reading ease': reading_ease,
						'Grade level': grade_level
					}, ignore_index=True)

		except Exception as e:  ### if there is some error in the reading content
			print(e)
			output_dataframe = output_dataframe.append(
				{
					'University name': university,
					'University SHC URL': shc,
					'Relevant content on all pages': content,
					'Count of keywords matching webpages on SHC': no_of_links,
					'Keywords matched webpages on SHC': links,
					'Total word count on all pages': total_words,
					'Reading ease': "Error in reading content!",
					'Grade level': "Error in reading content!"
				}, ignore_index=True)

	output_dataframe.to_csv(output_dir + '/Reading_level_of_content_without_pdf.csv')  ## storing results

	return output_dataframe
