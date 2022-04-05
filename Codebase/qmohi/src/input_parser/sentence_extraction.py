from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
from nltk.tokenize import sent_tokenize
import re
from bs4 import BeautifulSoup

def get_search_results(output_dir, keyword_list, margin):
	# Specify the path to cache data
	cache_dir_path = join(output_dir, "saved_webpages")
	cache_universities = [d for d in listdir(cache_dir_path) if isdir(join(cache_dir_path, d))]
	for cache_university in cache_universities:
		# Specify the path to each university's cache data
		cache_university_path = join(cache_dir_path, cache_university)
		cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
		if not cache_files:
			continue
	
		# Specify the sentence extraction output file path
		se_output_dir_path = join(output_dir, 'sentence_extraction_output')
		se_output_dir_path = join(se_output_dir_path, cache_university)
		
		# Read cache files and extract the anchor sentences
		for cache_file in cache_files:
			# Specify the path to each cache file
			cache_file_path = join(cache_university_path, cache_file)
			# Read the cache file
			fo_input = open(cache_file_path, 'r')
			text = fo_input.read()
			fo_input.close()

			se_output_file_path = join(se_output_dir_path, cache_file)
			makedirs(dirname(se_output_file_path), exist_ok=True)
			fo_output = open(se_output_file_path, 'w')
			fo_output.write('<h1 style="margin:2rem 5%">QMOHI Keyword Search Results</h1><p style="margin:2rem 5%">')

			# Clean the text data
			bs_obj = BeautifulSoup(text, 'html.parser')
			text = bs_obj.get_text()
			# Segment the sentences
			sentences = sent_tokenize(text)
			# Add space to the end of the sentence for the readability in output file
			#sentences = [sentence + " " for sentence in sentences]
			sentences = [re.sub(r' +', ' ', sentence) for sentence in sentences]
			sentences = [re.sub(r'\n+', '<br>', sentence) + " " for sentence in sentences]
			#print(sentences)

			MARGIN = 1
			ANCHOR = 2
			anchor_sentence_ref = [0] * len(sentences)
			for i, sentence in enumerate(sentences):
				if any(keyword in sentence.lower() for keyword in keyword_list):
					for j in range(i-margin, i+margin+1):
						if j < 0 or j >= len(sentences):
							continue
						if j == i:
							anchor_sentence_ref[j] = ANCHOR
						elif anchor_sentence_ref[j] != ANCHOR:
							anchor_sentence_ref[j] = MARGIN

			re_keywords = "|".join(keyword_list)
			for i, sentence in enumerate(sentences):
				if anchor_sentence_ref[i] == ANCHOR:
					anchor_word_indices = [(m.start(), m.end()) for m in re.finditer(re_keywords, sentence.lower())]
					if anchor_word_indices:
						anchor_sentence_html = '<span style="background-color:#fff352;">'
						anchor_sentence_cursor = 0
						for start, end in anchor_word_indices:
							anchor_sentence_html += sentence[anchor_sentence_cursor:start] + '<b style="color:red;">' + sentence[start:end] + '</b>'
							anchor_sentence_cursor = end
						anchor_sentence_html += sentence[end:] + '</span>'
				elif anchor_sentence_ref[i] == MARGIN:
					anchor_sentence_html = '<span style="background-color:#CEECF5;">' + sentence + '</span>'
				else:
					anchor_sentence_html = sentence
				# Export into output file
				fo_output.write(anchor_sentence_html)

		fo_output.write('</p>')
		fo_output.close()
