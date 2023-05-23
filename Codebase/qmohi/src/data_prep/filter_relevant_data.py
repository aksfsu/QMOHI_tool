"""
Find data relevant to the keywords from the data retrieved from program retrieved URLs
Input - all data retrieved from the URLs
Output - data relevant to the keywords
"""
from nltk.text import Text
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
import nltk.corpus
import pandas as pd
import os
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
import re
from bs4 import BeautifulSoup

from PyPDF2 import PdfReader
from tempfile import TemporaryDirectory
from pdf2image import convert_from_path
import easyocr

nltk.download('gutenberg')  # Can be run only once in the beginning


def get_text_from_image(image_path):
	# Extract text
	reader = easyocr.Reader(['en'], verbose=False)
	try:
		# Consider each segment as a sentence by adding ". "
		texts = reader.readtext(image_path, detail=0)
	except:
		return ""
	return ". ".join(texts)


def get_text_in_images_from_html(html):
	soup = BeautifulSoup(html, 'html.parser')
	images = soup.find_all('img')
	text = ""
	if len(images) > 0:
		for image in images:
			image_link = ""
			try:
				image_link = image["src"]
			except:
				try:
					image_link = image["data-srcset"]
				except:
					try:
						image_link = image["data-src"]
					except:
						try:
							image_link = image["data-fallback-src"]
						except:
							pass

			if image_link:
				try:
					text += " " + get_text_from_image(image_link)
				except:
					pass
	return text


def get_text_from_pdf(pdf_path):
	text = ""

	reader = PdfReader(pdf_path)
	for page in reader.pages:
		raw_text = page.extract_text()
		try:
			images = page.images
		except:
			images = []
		for image in images:
			with TemporaryDirectory() as tempdir:
				file_path = join(tempdir, image.name)
				with open(file_path, "wb") as fp:
					fp.write(image.data)
				raw_text += " " + get_text_from_image(file_path)

		if raw_text:
			raw_text = re.sub(r"  +", ". ", raw_text)
			raw_text = raw_text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
			text += ". " + raw_text

	if not text:
		with TemporaryDirectory() as tempdir:
			# Converting PDF to images
			pdf_pages = convert_from_path(pdf_path, 500)[:5] # up to 5 pages
			image_file_list = []
			for i, page in enumerate(pdf_pages, start=1):
				file_path = join(tempdir, f"page_{i}.jpg")
				page.save(file_path, "JPEG")
				image_file_list.append(file_path)

			# Recognizing text from the images using OCR
			for image_file in image_file_list:
				try:
					text += " " + get_text_from_image(image_file)
				except:
					pass

	return text


def relevant_content_words(keywords, file):
	content = Text(nltk.corpus.gutenberg.words(file))
	tokens = content.tokens

	# Concordance referred from https://simplypython.wordpress.com/2014/03/14/saving-output-of-nltk-text-concordance/
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


def clean_text(text):
	# Remove URLs
	text = re.sub(r"http\S+", "", text, flags=re.MULTILINE)
	text = re.sub(r"www\S+", "", text, flags=re.MULTILINE)
	# Remove redundant dots and new lines
	text = re.sub(r"[\n ]+\.", "", text)
	text = re.sub(r"\. +\.", ".", text)
	text = re.sub(r"\.+", ".", text)
	# Remove redundant white spaces
	text = re.sub(r" +", " ", text)
	return text


def sentence_highlight(se_output_file_path, text, keywords, margin):
	topical_contents = []
	text = clean_text(text)

	# Open the output file
	fo_output = open(se_output_file_path, 'a')

	# sent_tokenize() separates sentences by ". "
	sentences = [sentence for sentence in sent_tokenize(text) if re.search(r"\w", sentence)]

	# Add space to the end of the sentence for the readability in output file
	sentences = [re.sub(r'\n+', '<br>', sentence) for sentence in sentences]

	# Create a reference list whole elements indicates margin and anchor sentences
	MARGIN = 1
	ANCHOR = 2
	anchor_sentence_ref = [0] * len(sentences)
	for i, sentence in enumerate(sentences):
		if any(keyword.lower() in sentence.lower() for keyword in keywords):
			for j in range(i-margin, i+margin+1):
				# Ignore if the index is out of bounds
				if j < 0 or j >= len(sentences):
					continue
				# Mark as anchor sentence if keyword matches
				if j == i:
					anchor_sentence_ref[j] = ANCHOR
				# Mark as margin sentence if the sentence is in the range of margin and not an anchor sentence
				elif anchor_sentence_ref[j] != ANCHOR:
					anchor_sentence_ref[j] = MARGIN

	# Convert the keyword list into regex format
	re_keywords = "|".join(sorted(keywords, key=len, reverse=True))
	# Highlight margin and anchor sentences and keywords
	for i, sentence in enumerate(sentences):
		sentence += " "
		# Highlight anchor sentences
		if anchor_sentence_ref[i] == ANCHOR:
			cleaned_text = sentence.replace("<br>", "")
			if cleaned_text:
				topical_contents.append(cleaned_text)
			# Find the start and end indices of keywords
			anchor_word_indices = [(m.start(), m.end()) for m in re.finditer(re_keywords, sentence, re.IGNORECASE)]
			if anchor_word_indices:
				anchor_sentence_html = '<span style="background-color:#fff352;">'
				# Highlight keywords
				anchor_sentence_cursor = 0
				for start, end in anchor_word_indices:
					anchor_sentence_html += sentence[anchor_sentence_cursor:start] + '<b style="color:red;">' + sentence[start:end] + '</b>'
					anchor_sentence_cursor = end
				anchor_sentence_html += sentence[end:] + '</span>'
		# Highlight margin sentences
		elif anchor_sentence_ref[i] == MARGIN:
			cleaned_text = sentence.replace("<br>", "")
			if cleaned_text:
				topical_contents.append(cleaned_text)
			anchor_sentence_html = '<span style="background-color:#CEECF5;">' + sentence + '</span>'
		# Leave other sentences without highlighting
		else:
			anchor_sentence_html = sentence
		# Export into output file
		fo_output.write(anchor_sentence_html)

	# End the result paragraph and close the file
	fo_output.write('<br>')
	fo_output.close()

	return topical_contents


# Collect topical information and highlight it in copies of cached HTML files
def get_topical_contents(output_dir, university, keywords, margin=5):
	# Raw topical sentence data to return
	topical_contents = []

	# Specify the path to cache data
	cache_dir_path = join(output_dir, "saved_webpages")
	cache_university_path = join(cache_dir_path, university)
	if isdir(cache_university_path):
		cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
		if not cache_files:
			return topical_contents

		# Specify the sentence extraction output file path
		se_output_dir_path = join(output_dir, 'sentence_extraction_output')
		se_output_dir_path = join(se_output_dir_path, university)
		
		# Read cache files and extract the anchor sentences
		for cache_file in cache_files:
			# Specify the path to each cache file
			cache_file_path = join(cache_university_path, cache_file)

			# Extract text
			if cache_file.endswith("pdf"):
				text = get_text_from_pdf(cache_file_path).encode("ascii", "ignore").decode()
			else:
				try:
					fo_input = open(cache_file_path, 'r')
					html = fo_input.read()
				except:
					continue
				finally:
					fo_input.close()

				bs_obj = BeautifulSoup(html, 'html.parser')
				text = bs_obj.get_text(". ").encode("ascii", "ignore").decode()
				text += get_text_in_images_from_html(html)

			# Run sentence highlight
			se_output_file_path = join(se_output_dir_path, os.path.splitext(cache_file)[0] + ".html")
			makedirs(dirname(se_output_file_path), exist_ok=True)
			topical_contents.extend(sentence_highlight(se_output_file_path, text, keywords, margin))

	return topical_contents


def add_space_in_keywords(keywords):
	return [keyword.replace("-", " - ") for keyword in keywords]


# Find relevant content from the data provided on the basis of keywords
def find_relevant_content(input_dataframe, keywords, margin, output_dir):
	header = ['University name', 'University SHC URL', 'Count of SHC webpages matching keywords',
			  'Keywords matched webpages on SHC', 'Total word count on all pages', 'Relevant content on all pages']
	output_dataframe = pd.DataFrame(columns=header)
	phrase_stem_dictionary = []
	list_of_found_per_stem_dictionary = []
	list_of_stem_found_phrase_dictionary = []

	# Add flexibility to keywords
	lemmatizer = WordNetLemmatizer()
	keywords.extend([lemmatizer.lemmatize(keyword) for keyword in keywords if lemmatizer.lemmatize(keyword) not in keywords])
	spaced_keywords = add_space_in_keywords(keywords)

	print("Universities where keywords relevant information was found:")

	# For every university in the dataframe
	for index, row in input_dataframe.iterrows():
		found_per_stem_dictionary = []
		stem_found_phrase_dictionary = []
		university = row['University name']
		shc = row['University SHC URL']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']

		print("- ", university)

		# Collect topical information
		contents = get_topical_contents(output_dir, university, keywords, margin)

		if contents:
			# Calculating total number of words on all web pages
			total_words = sum(len(content.split()) for content in contents)
	
			# Try writing content in the text file
			try:
				relevant_content_file = output_dir + "/relevant_content.txt"
				out_file = open(relevant_content_file, 'w')
				out_file.write(" ".join(contents))
				out_file.close()

				# Words_content here is list of lists
				found_per_stem_dictionary, phrase_stem_dictionary, stem_found_phrase_dictionary = relevant_content_words(spaced_keywords, relevant_content_file)

				# Deleting relevant_file.txt
				os.remove(relevant_content_file)

			except Exception as e:
				print(e)

			list_of_found_per_stem_dictionary.append(found_per_stem_dictionary)
			list_of_stem_found_phrase_dictionary.append(stem_found_phrase_dictionary)
			output_dataframe = output_dataframe.append({'University name': university,
														'University SHC URL': shc,
														'Count of SHC webpages matching keywords': no_of_links,
														'Keywords matched webpages on SHC': link_data,
														'Relevant content on all pages': contents,
														'Total word count on all pages': total_words
														}, ignore_index=True)

	# Storing output dataframe
	output_dataframe.to_csv(output_dir + '/get_relevant_data_from_collected_data.csv')

	# Returning output dataframe and space added keywords for metric calculation
	return output_dataframe, spaced_keywords, list_of_found_per_stem_dictionary, phrase_stem_dictionary, list_of_stem_found_phrase_dictionary
