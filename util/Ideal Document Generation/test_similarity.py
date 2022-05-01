import re
import numpy as np
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
import csv
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize

from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

WORD_VECTOR_PATH = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/GoogleNews-vectors-negative300.bin"

# Get text from the text file
def get_text_from_file(file_path):
    # Open the output file
    with open(file_path, 'r') as f:
        text = f.read()
    return text

# Get text from the HTML file
def get_text_from_html_file(file_path):
    # Open the output file
    with open(file_path, 'r') as f:
        html = f.read()

    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator=" ", strip=True)

# Preprocess the document
def preprocess_document(doc):
    # Remove URLs
    doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
    doc = re.sub(r'www\S+', '', doc, flags=re.MULTILINE)
    # Remove stop words
    doc = remove_stopwords(doc)
    # Remove punctuation
    doc = strip_punctuation(doc)
    # Remove non-alphanumeric characters
    doc = strip_non_alphanum(doc)
    # Remove numeric characters
    doc = strip_numeric(doc)
    # Remove redundant white spaces
    doc = strip_multiple_whitespaces(doc)
    return doc

# Tokenize the document
def get_token_list(doc):
    # Data cleaning
    doc = preprocess_document(doc)
    return list(tokenize(doc, to_lower=True, deacc = True))

# Calculate the similarity based on the given word vector
def calculate_similarity(word_vector, doc1, doc2):
    # sum1 will hold the sum of all of its word's vectors
    sum1 = [0] * len(word_vector['word'])
    for token in get_token_list(doc1):
        if token in word_vector:
            sum1 = np.sum([sum1, word_vector[token]], axis=0)

    # sum2 will hold the sum of all of its word's vectors
    sum2 = [0] * len(word_vector['word'])
    for token in get_token_list(doc2):
        if token in word_vector:
            sum2 = np.sum([sum2, word_vector[token]], axis=0)

    # Calculate the cosine similarity
    similarity = cosine_similarity([sum1], [sum2])
    return similarity[0][0]

def calculate_tfidf():
    EXPERIMENTAL_TERMS = [
        "Accidental Injury",
        "First Aid",
        "Allergy",
        "Cold",
        "Vaccines",
    ]

    shc_corpora = []
    id_corpora = []

    # Run tests over the cache data of SHC websites
    cache_dir_path = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/output/Second Run/saved_webpages"
    cache_universities = [d for d in listdir(cache_dir_path) if isdir(join(cache_dir_path, d))]
    for cache_university in cache_universities:
        # Build the path to each university's cache data
        cache_university_path = join(cache_dir_path, cache_university)
        cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
        if not cache_files:
            continue

        # Read cache files
        for cache_file in cache_files:
            # Specify the path to each cache file
            cache_file_path = join(cache_university_path, cache_file)
            # Add to corpora
            shc_corpora.append(get_text_from_html_file(cache_file_path))

    for term in EXPERIMENTAL_TERMS:
        # Add to corpora
        id_corpora.append(get_text_from_file(join("./output", term + '.txt')))

    ctfidf = CustomizableTfidfVectorizer(shc_corpora, id_corpora)
    print(ctfidf.rank_tfidf(-5))

    return

def main():
    '''
    with open(join("./output", 'Medicated Abortion.txt'), 'r') as f:
        doc1 = f.read()

    with open(join("./output", 'Abortion.txt'), 'r') as f:
        doc2 = f.read()
    '''

    # calculate_tfidf()

    # Load the word vector
    print("Loading model...")
    word_vector = KeyedVectors.load_word2vec_format(WORD_VECTOR_PATH, binary=True)
    print("Loaded")

    EXPERIMENTAL_TERMS = [
        "Accidental Injury",
        "First Aid",
        "Allergy",
        "Cold",
        "Vaccines",
    ]

    for term in EXPERIMENTAL_TERMS:
        # Open the output file
        output_file_path = "./similarity_experiment_term=" + term + ".csv"
        makedirs(dirname(output_file_path), exist_ok=True)
        output_file = open(output_file_path, 'a')
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['University', 'Cache File Name', 'Similarity'])

        # Run tests over the cache data of SHC websites
        cache_dir_path = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/output/Second Run/saved_webpages"
        cache_universities = [d for d in listdir(cache_dir_path) if isdir(join(cache_dir_path, d))]
        for cache_university in cache_universities:
            # Build the path to each university's cache data
            cache_university_path = join(cache_dir_path, cache_university)
            cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
            if not cache_files:
                continue

            # Read cache files
            for cache_file in cache_files:
                # Specify the path to each cache file
                cache_file_path = join(cache_university_path, cache_file)
                # Calculate similarity between the ideal document and a cached SHC website
                similarity = calculate_similarity(word_vector, 
                    get_text_from_file(join("./output", term + '.txt')), 
                    get_text_from_html_file(cache_file_path)
                )
                csv_writer.writerow([cache_university, cache_file, similarity])
                print(f'{cache_university}/{cache_file}: {round(similarity * 100, 3)}% ({similarity})')

    output_file.close()
    return

if __name__ == "__main__":
    main()