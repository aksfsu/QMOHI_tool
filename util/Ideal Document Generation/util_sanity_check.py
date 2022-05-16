import re
import numpy as np
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname, exists
import csv
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize

WORD_VECTOR_PATH = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/GoogleNews-vectors-negative300.bin"
STOPWORD_FILE_PATH = "./stopwords"

# Get text from the text file
def get_text_from_file(file_path):
    # Open the output file
    with open(file_path, 'r') as f:
        text = f.read()
    return text

def remove_optional_stopwords(doc):
    stopword_file_paths = [join(STOPWORD_FILE_PATH, f) for f in listdir(STOPWORD_FILE_PATH) if isfile(join(STOPWORD_FILE_PATH, f)) and f.startswith("stopwords")]

    doc = list(tokenize(doc, to_lower=True, deacc = True))
    # print(f'before: {len(doc)}')
    # Read stopword files
    for stopword_file_path in stopword_file_paths:
        with open(stopword_file_path, 'r') as f:
            stopwords = f.read()
            doc = [word for word in doc if word not in stopwords]
    # print(f'after: {len(doc)}')
    return " ".join(doc)

# Preprocess the document
def preprocess_document(doc):
    # Remove URLs
    doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
    doc = re.sub(r'www\S+', '', doc, flags=re.MULTILINE)
    # Remove stop words
    doc = remove_stopwords(doc)
    doc = remove_optional_stopwords(doc)
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
def get_token_list(doc, doc_name=None):
    # Data cleaning
    doc = preprocess_document(doc)
    return list(tokenize(doc, to_lower=True, deacc = True))

# Calculate the similarity based on the given word vector
def calculate_similarity(word_vector, doc1, doc2, doc_name1=None, doc_name2=None):
    # sum1 will hold the sum of all of its word's vectors
    sum1 = [0] * len(word_vector['word'])
    for token in get_token_list(doc1, doc_name1):
        if token in word_vector:
            sum1 = np.sum([sum1, word_vector[token]], axis=0)

    # sum2 will hold the sum of all of its word's vectors
    sum2 = [0] * len(word_vector['word'])
    for token in get_token_list(doc2, doc_name2):
        if token in word_vector:
            sum2 = np.sum([sum2, word_vector[token]], axis=0)

    # Calculate the cosine similarity
    similarity = cosine_similarity([sum1], [sum2])
    return similarity[0][0]

def main():
    EXPERIMENTAL_TERMS = [
        "Accidental Injury",
        "First Aid",
        "Allergy",
        "Cold",
        "Vaccines",
        "Abortion",
        "Medicated Abortion",
        "lorem_ipsum_10",
        "lorem_ipsum_5",
        "lorem_ipsum_3",
        "consumer_credit_card_agreement",
    ]

    # Load the word vector
    print("Loading model...")
    word_vector = KeyedVectors.load_word2vec_format(WORD_VECTOR_PATH, binary=True)
    print("Loaded")

    # Open the output file
    output_file_path = "./similarity_sanity_check_experiment.csv"
    makedirs(dirname(output_file_path), exist_ok=True)
    output_file = open(output_file_path, 'w')
    csv_writer = csv.writer(output_file)
    csv_writer.writerow(['File 1', 'File 2', 'Similarity'])

    for term1 in EXPERIMENTAL_TERMS:
        for term2 in EXPERIMENTAL_TERMS:
            # Calculate similarity between the ideal document and a cached SHC website
            similarity = calculate_similarity(word_vector, 
                get_text_from_file(join("./output", term1 + '.txt')), 
                get_text_from_file(join("./output", term2 + '.txt')), 
            )
            csv_writer.writerow([term1, term2, similarity])
            print(f'{term1}:{term2} | {round(similarity * 100, 3)}% ({similarity})')

    output_file.close()
    return

if __name__ == "__main__":
    main()