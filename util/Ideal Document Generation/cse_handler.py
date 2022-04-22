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

			# Add the retrieved results to the return list
			if 'items' not in response:
				print("   - Not found")
			else:
				for item in response['items']:
					links.append(item['link'])

		except Exception as e:
			print("Caught exception for Custom Search engine!", e)

		return links
