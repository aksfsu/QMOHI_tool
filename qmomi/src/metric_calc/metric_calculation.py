# i.Objectivity
# iii.Timeliness
# iv.Similarity


from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
import requests
import re
from urllib.parse import urlparse
from qmomi.src.metric_calc.navigation_metric.Counter import get_min_click_count
import datetime


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

		print(polarity)
		return round(polarity, 3)

	def calculate_sentiment_objectivity(self):

		university_content = self.content

		objectivity = 1 - TextBlob(university_content).subjectivity

		print(objectivity)
		return round(objectivity, 3)

	def calculate_timeliness(self):

		timeliness = []

		# links_list = re.findall(r"'(.*?)'", self.links)  # for converting links string into links list
		# for url in links_list:

		# print(links_list)
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
						print("Data is not available")
						last_modified = -1
				else:
					last_modified = -1

				timeliness.append(last_modified)

			except Exception as e:
				print("Unable to get the header. Error - ", e)
				return -1

		print("\n\nTimeliness:", timeliness)
		return timeliness

	def calculate_similarity(self, ideal_content):

		university_content = self.content

		# because ideal content should match with the relevant content
		non_alphabets_list = ['_', '-', ':']
		for every_item in non_alphabets_list:
			replacing_item = " " + every_item + " "
			ideal_content = re.sub(every_item, replacing_item, ideal_content)
			# ideal_content = ideal_content.replace(every_item, replacing_item)
		# print("-------------------------> Ideal content : ", ideal_content)

		# file = open( "/Users/tejasvibelsare/Library/Mobile
		# Documents/com~apple~CloudDocs/Code/Generic_new/data/all_contraception_fake_document.txt")
		#
		# fake_document = file.read()  # .replace("\n", " ")
		#
		# # print(fake_document)
		# file.close()

		corpus = [ideal_content, university_content]

		vectorizer = TfidfVectorizer()
		trsfm = vectorizer.fit_transform(corpus)
		answer = pd.DataFrame(trsfm.toarray(), columns=vectorizer.get_feature_names(),
							  index=['fake_document', 'university_content'])

		print(answer)

		# similarity = cosine_similarity(trsfm[0:1], trsfm)
		similarity = cosine_similarity(trsfm[0], trsfm[1])
		print("\n Similarity:", similarity)

		# to get the similarity with the content with fake document
		# print(similarity[0,1])
		return round(similarity[0][0], 3)

	'''
	def calculate_navigation(self, navigation_dataframe):

		try:
			nav_row = navigation_dataframe.loc[
				navigation_dataframe['Uni Name'] == self.uni_name, '#of Clicks']  # .iloc[0]

			print(nav_row)

			nav = navigation_dataframe.loc[navigation_dataframe['Uni Name'] == self.uni_name, '#of Clicks'].iloc[0]

			print(nav)

			return nav

		except Exception as e:
			print("Error :", e)
			return -1
	'''

	def calculate_navigation(self):

		timestamp_start = datetime.datetime.now()
		min_clicks, trace = get_min_click_count(self.no_of_links, self.links, self.shc_url)
		timestamp_end = datetime.datetime.now()
		if min_clicks == (999, []):
			return -1, [], timestamp_start, timestamp_end
			# return -1, []
		return min_clicks, trace, timestamp_start, timestamp_end
		# return min_clicks, trace


def calculate_metrics(input_dataframe, output_dir, ideal_doc):
	# input_dataframe = pd.read_csv("/Users/tejasvibelsare/Desktop/input_for_calculating_extra_parameters.csv")
	# input_dataframe = pd.read_csv(
	# 	"/Users/tejasvibelsare/Desktop/all_contraception/Output 2020-07-09 19:04:46/get_relevant_data_from_collected_data_without_pdf_links.csv")

	header = ['University name', 'Count of keywords matching webpages on SHC', 'Keywords matched webpages on SHC',
			  'Content on all pages',
			  'Similarity', 'Sentiment objectivity', 'Sentiment polarity', 'Timeliness', 'Navigation', 'Trace',
			  'timestamp_start', 'timestamp_end']
	output_dataframe = pd.DataFrame(columns=header)

	# navigation_dataframe = pd.read_excel(
	# 	"/Users/tejasvibelsare/Library/Mobile Documents/com~apple~CloudDocs/Spring 2020/CSC 895/Risha Compiled data for 151 Universities.xlsx",
	# 	usecols=['Uni Name', '#of Clicks'])

	file = open(ideal_doc)
	ideal_content = file.read()  # .replace("\n", " ")
	# print(ideal_content)
	file.close()

	for index, row in input_dataframe.iterrows():
		uni_name = row['University name']
		no_of_links = row['Count of keywords matching webpages on SHC']
		links = row['Keywords matched webpages on SHC']
		content = row['Relevant content on all pages']
		shc_url = row['University SHC URL']

		obj = University(uni_name, shc_url, content, links, no_of_links)

		similarity = obj.calculate_similarity(ideal_content)

		sentiment_objectivity = obj.calculate_sentiment_objectivity()

		sentiment_polarity = obj.calculate_sentiment_polarity()

		timeliness = obj.calculate_timeliness()

		navigation, trace, timestamp_start, timestamp_end = obj.calculate_navigation()
		# navigation, trace = obj.calculate_navigation()

		# navigation = obj.calculate_navigation(navigation_dataframe)
		# navigation = -1			#### currently navigation is available only for LARC

		output_dataframe = output_dataframe.append({'University name': uni_name,
													'Count of keywords matching webpages on SHC': no_of_links,
													# 'Keywords matched webpages on SHC': links,
													# links is getting edited somewhere in the code of nmeasures calculation
													'Keywords matched webpages on SHC': row[
														'Keywords matched webpages on SHC'],
													'Content on all pages': content,
													'Similarity': similarity,
													'Sentiment objectivity': sentiment_objectivity,
													'Sentiment polarity': sentiment_polarity,
													'Timeliness': timeliness,
													'Navigation': navigation,
													'Trace': trace,
													'timestamp_start': timestamp_start,
													'timestamp_end': timestamp_end
													}, ignore_index=True)

	# output_dataframe.to_csv(
	# 	'/Users/tejasvibelsare/Desktop/all_contraception/Output 2020-07-09 19:04:46/measures_result.csv')  ## storing result

	output_dataframe.to_csv(output_dir + '/measures_result.csv')  ## storing output

	return output_dataframe
