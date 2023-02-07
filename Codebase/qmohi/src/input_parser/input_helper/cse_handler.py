from googleapiclient.discovery import build
import json
import time

class CSEHandler:
	def __init__(self, api_key, cse_id):
		self.api_key = api_key
		self.cse_id = cse_id

	# Get links containing the term
	def get_links_by_query(self, url, term):
		links = []

		# Preparing query with the given term
		query = term + " site:" + url

		# Google API custom search service
		time.sleep(1)
		try:
			service = build("customsearch", "v1", developerKey=self.api_key)
			response = service.cse().list(
				q=query,
				cx=self.cse_id,
				lr='lang_en',
			).execute()
			
			# Output received in the form of json
			with open('data.json', 'w') as outfile:
				json.dump(response, outfile)

			# Items contain all the retrieved results
			if 'items' in response:
				for item in response['items']:
					if item['link'].endswith(".pdf") or\
					   'mime' in item and 'pdf' in item['mime'].lower() or\
					   'fileFormat' in item and 'pdf' in item['fileFormat'].lower():
						content_format = 'pdf'
					elif item['link'].endswith(".doc") or item['link'].endswith(".docx"):
						# MS Word format is not supported
						continue
					else:
						content_format = 'html'
					
					# Links from the items contain URLs
					links.append({'url': item['link'], 'format': content_format})

		except Exception as e:
			print("Caught exception for Custom Search engine!", e)

		return links
