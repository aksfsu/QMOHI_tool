import pandas as pd
from textblob import TextBlob
import requests
import re
from urllib.parse import urlparse
from qmohi.src.metric_calc.navigation_metric.counter import get_min_click_count
from gensim.models import KeyedVectors
from gensim.test.utils import datapath

from qmohi.src.metric_calc.similarity_metric.similarity import Similarity

class University:

	def __init__(self, uni_name, shc_url, content, links, no_of_links):
		self.uni_name = uni_name
		self.shc_url = shc_url
		self.content = content
		self.links = links
		self.no_of_links = no_of_links

	def calculate_sentiment_polarity(self):

		university_content = self.content
		polarity = TextBlob(university_content).polarity
		return round(polarity, 3)

	def calculate_sentiment_objectivity(self):

		university_content = self.content
		objectivity = 1 - TextBlob(university_content).subjectivity
		return round(objectivity, 3)

	def calculate_timeliness(self):

		timeliness = []

		if isinstance(self.links, str):
			self.links = re.findall(r"'(.*?)'", self.links)

		for url in self.links:
			result = urlparse(url)

			try:
				if True if [result.scheme, result.netloc, result.path] else False:
					header = requests.head(url).headers
					if 'Last-Modified' in header:
						last_modified = header['Last-Modified']
					else:
						# Last-modified information is not available
						last_modified = -1
				else:
					last_modified = -1

				timeliness.append(last_modified)

			except Exception as e:
				print("Unable to get the header of the web page. Error - ", e)
				return -1

		return timeliness

	def calculate_similarity(self, word_vector, comparison_doc_path):
		# Load the comparison document
		file = open(comparison_doc_path)
		comparison_content = file.read()
		file.close()

		# Calculate similarity
		similarity_obj = Similarity(word_vector)
		similarity, similarity_label = similarity_obj.calculate_similarity(comparison_content, self.content)
		return round(similarity, 3), similarity_label

	def calculate_navigation(self, driver_path):

		min_clicks, trace = get_min_click_count(self.no_of_links, self.links, self.shc_url, driver_path)
		if min_clicks == (999, []):
			return -1, []
		return min_clicks, trace


def calculate_metrics(input_dataframe, output_dir, comparison_doc_path, driver_path, model_path):

	header = ['University name', 'Count of SHC webpages matching keywords', 'Keywords matched webpages on SHC',
			  'Content on all pages', 'Similarity Score', 'Similarity Label', 'Sentiment objectivity', 'Sentiment polarity', 'Timeliness',
			  'Navigation', 'Trace']
	output_dataframe = pd.DataFrame(columns=header)

	# If the model_path is 0, that means a model was not provided. Old method for similarity will be used.
	if (model_path != 0):
		print("Loading model...")
		wv = KeyedVectors.load_word2vec_format(datapath(model_path), binary=True)
		print("Loaded")

	for index, row in input_dataframe.iterrows():

		uni_name = row['University name']
		no_of_links = row['Count of SHC webpages matching keywords']
		link_data = row['Keywords matched webpages on SHC']
		links = [data["url"] for data in link_data]
		content = row['Relevant content on all pages']
		shc_url = row['University SHC URL']
		print("\n- ", uni_name)

		obj = University(uni_name, shc_url, content, links, no_of_links)

		print("   - Similarity")
		similarity, similarity_label = obj.calculate_similarity(wv, comparison_doc_path)

		print("   - Objectivity")
		sentiment_objectivity = obj.calculate_sentiment_objectivity()

		print("   - Polarity")
		sentiment_polarity = obj.calculate_sentiment_polarity()

		print("   - Timeliness")
		timeliness = obj.calculate_timeliness()

		print("   - Navigation")
		navigation, trace = obj.calculate_navigation(driver_path)
		
		output_dataframe = output_dataframe.append({'University name': uni_name,
													'Count of SHC webpages matching keywords': no_of_links,
													'Keywords matched webpages on SHC': row['Keywords matched webpages on SHC'],
													'Content on all pages': content,
													'Similarity Score': similarity,
													'Similarity Label': similarity_label,
													'Sentiment objectivity': sentiment_objectivity,
													'Sentiment polarity': sentiment_polarity,
													'Timeliness': timeliness,
													'Navigation': navigation,
													'Trace': trace
													}, ignore_index=True)
		
	# Storing output
	output_dataframe.to_csv(output_dir + '/measures_result.csv')

	return output_dataframe
