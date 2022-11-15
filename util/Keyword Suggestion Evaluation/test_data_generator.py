import sys

from bs4 import BeautifulSoup
from os import makedirs
import re
import requests
from collections import Counter
import pandas as pd
from os import listdir
from os.path import isfile, join, dirname

from nltk.stem import WordNetLemmatizer

import asyncio
import pyppeteer


# Config constants
PUBMED_URL_BASE = "https://pubmed.ncbi.nlm.nih.gov/"
PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=30&sort=relevance&retmode=json&term="

TEST_DATA_PATH = "keyword_suggestion_test_data.csv"


# Access websites based on the given URL
async def get_html_from_url(url):
    # print(url)
    browser = await pyppeteer.launch({
        'args': ['--no-sandbox', '--disable-dev-shm-usage']
    })
    page = await browser.newPage()
    await page.goto(url)
    html = await page.content()
    await browser.close()
    return html


# Get text data and export in the output file
def get_keywords(url):
    # Get the HTML based on URL
    html = asyncio.get_event_loop().run_until_complete(get_html_from_url(url))
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    abstract = soup.find(id="eng-abstract")
    if abstract:
        keywords = ""
        for sibling in abstract.next_siblings:
            keywords = sibling.get_text(separator=" ", strip=True)
            if keywords.startswith("Keywords:"):
                keywords = keywords[10:]
                keywords = re.sub(r'[\(\)]', r";", keywords)
                keywords = re.sub(r' – ', r";", keywords)
                keywords = re.sub(r'["\./,-]', " ", keywords)
                keywords = keywords.replace(" +", " ")
                keywords = keywords.replace("&", "and")
                keywords = [k.strip().lower() for k in keywords.split(";") if len(k.strip()) >= 3]
                print(f'{url}: {keywords}')
                return keywords
    return []


def get_pubmed_ids(query_term):
    if query_term.count(" ") > 0:
        query_term = "+".join(query_term.split())
    query = PUBMED_API_BASE + query_term

    response = requests.get(query)
    pubmed_json = response.json()
    return [paperId for paperId in pubmed_json["esearchresult"]["idlist"]]
    

def generate_test_data(output_file_path, topic):
    # Open the output file
    makedirs(dirname(output_file_path), exist_ok=True)

    pubmed_ids = get_pubmed_ids(topic)

    keyword_candidates = Counter()
    for pubmed_id in pubmed_ids:
        keyword_candidates.update(get_keywords(PUBMED_URL_BASE + pubmed_id))

    keywords = [topic.lower()]
    for keyword, count in keyword_candidates.items():
        if count >= 2 and keyword not in keywords:
            keywords.append(keyword)
    keywords = keywords[1:]
    
    df = pd.DataFrame({
		'Topic': [topic],
		'Keywords': [keywords]
	})
    df.to_csv(output_file_path, mode='a', index=False, header=False)

    return keywords[1:] # Return only keyword, not the topic


def strToList(str_data):
    str_data = str_data.lower()
    str_data = str_data.replace("'", "")
    str_data = str_data.replace("[", "")
    str_data = str_data.replace("]", "")
    return str_data.split(", ")


def load_test_data():
    df = pd.read_csv(join("./", TEST_DATA_PATH), usecols=['topic', 'pgs_keywords'])
    test_data_dct = {}
    for index, row in df.iterrows():
        test_data_dct[row['topic'].lower()] = strToList(row['pgs_keywords'])
    return test_data_dct


def get_input_keywords(intput_path):
    # Read the content from user's input file
    try:
        intput_df = pd.read_csv(intput_path, usecols=['University_name', 'Keywords', 'API_keys', 'Paid_API_key', 'CSE_id', 'Selenium_Chrome_webdriver',
                                                    'Output_directory', 'Ideal_document', 'Word_vector_model', 'Sentence_extraction_margin'])
    except Exception as e:
        print(e)
        exit()

    # Reading keywords provided by user
    keywords = intput_df[['Keywords']].copy()
    # Dropping rows with NaN values
    keywords = keywords.dropna(axis=0, how='any')

    if keywords.empty:
        print("Please provide keywords to look for!")
        exit()

    keywords = keywords.apply(lambda x:x.str.strip())
    keywords = keywords.apply(lambda x:x.str.replace(r' +', ' ', regex=True))
    keywords = keywords.apply(lambda x:x.str.lower())
    return keywords['Keywords'].tolist()


def test_coverage(keywords, gs_keywords):
    lemmatizer = WordNetLemmatizer()
    keywords = set([lemmatizer.lemmatize(keyword) for keyword in keywords])
    gs_keywords = set([lemmatizer.lemmatize(gs_keyword) for gs_keyword in gs_keywords])
    return sum(gs_keyword in keywords for gs_keyword in gs_keywords) / len(gs_keywords)


def evaluate_result(inpput_dir):
    result_file_paths = [join(inpput_dir, f) for f in listdir(inpput_dir) if f.endswith(".csv") and isfile(join(inpput_dir, f))]
    for file_path in result_file_paths:
        print(file_path)
        input_data = get_input_keywords(file_path)
        topic = input_data[0]

        test_data = load_test_data()
        if topic not in test_data:
            print(f"No test data for {topic}.")
            continue

        # Coverage Test
        coverage = test_coverage(input_data, test_data[topic])
        print(f"[{topic}] Coverage Test: {coverage}")
        df = pd.DataFrame({
            'Topic': [topic],
            'Time': [pd.Timestamp.today()],
            'Test Keywords': [test_data[topic]],
            'Input Keywords': [input_data],
            'Coverage': [round(coverage, 3)]
        })
        df.to_csv('test_result.csv', mode='a', index=False, header=False)


def batch_generate_test_data():    
    topics = [
        "Alcohol Addiction",
        "Alcohol Misuse",
        "Anorexia Nervosa",
        "Anxiety",
        "ADHD",
        "Birth Control",
        "Chlamydia",
        "Depression",
        "Domestic Violence",
        "Emergency Contraception",
        "Female Condoms",
        "Food Allergies",
        "Genital Herpes",
        "Gonorrhea",
        "Headaches",
        "Heatstroke",
        "Heroin",
        "HPV Vaccine",
        "Human Immunodeficiency Virus",
        "Influenza",
        "Insomnia",
        "Long Acting Reversible Contraception",
        "Measles",
        "Medicated abortion",
        "Meningitis",
        "Methamphetamine",
        "Irregular Periods",
        "Mononucleosis", # Mono
        "Obesity",
        "Pap Smear",
        "Pelvic Exam",
        "Premenstrual Syndrome", # PMS
        "Scoliosis",
        "Skin Cancer",
        "Smoking",
        "Suicidal Thoughts",
        "Syphilis",
        "Tobacco Addiction",
        "UTI",
        "Vaginitis",
    ]

    for topic in topics:
        # Auto generate test data
        print(f'[{topic}]')
        keywords = generate_test_data(join("./", TEST_DATA_PATH), topic)
        print(keywords)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Missing arguments.")
        exit()
    mode = sys.argv[1]
    if mode == "prep":
        batch_generate_test_data()
    elif mode == "eval":
        if len(sys.argv) < 3:
            print("Missing arguments.")
            exit() 
        evaluate_result(sys.argv[2])

