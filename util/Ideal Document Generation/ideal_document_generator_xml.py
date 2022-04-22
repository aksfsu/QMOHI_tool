from urllib.request import urlopen
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from os.path import join
import sys

def data_from_url(term):
	try:
		# Fetch the xml file for the term
		xml = urlopen("https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term="+term).read()
	
	# If problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		return None

	try:
		# Using xml parser for retrieving text
		return ET.fromstring(xml)

	# If problem in accessing URL
	except Exception as e:
		print("Exception : ", e)
		return None

# Build the search term string from commandline args 
term = "%20".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])
# Get the tree of Medline xml file
tree = data_from_url(term)
# Identify the summary of the term
documents = [d for d in tree.iter('document')]
for content in documents[0].findall('content'):
	if content.get('name') == "FullSummary":
		# Remove xml tags from the text
		bs_summary = BeautifulSoup(content.text, "html.parser")
		summary = bs_summary.get_text()
		#print(f'summary: {summary}')
		break

# Export into a text file
f_output = open(join("./", term.replace("%20", " ") + ".txt"), 'w')
f_output.write(summary)
f_output.close()