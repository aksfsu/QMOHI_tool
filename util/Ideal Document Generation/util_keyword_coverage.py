import re
import sys
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd

from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

INPUT_PATH = "./output"
STOPWORD_FILE_PATH = "./stopwords"
HEALTH_TOPICS_PATH = "./health_topics_summary"
CACHE_DIR_PATH = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/output/Second Run/saved_webpages"
KEYWORD_DIR_PATH = "./keywords"

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

def remove_stopwords(doc):
    stopword_file_paths = [join(STOPWORD_FILE_PATH, f) for f in listdir(STOPWORD_FILE_PATH) if isfile(join(STOPWORD_FILE_PATH, f)) and f.startswith("stopwords")]

    doc = list(tokenize(doc, to_lower=True, deacc = True))

    # Read stopword files
    for stopword_file_path in stopword_file_paths:
        with open(stopword_file_path, 'r') as f:
            stopwords = f.read()
            doc = [word for word in doc if word not in stopwords]
    return " ".join(doc)

# Preprocess the document
def preprocess_document(doc, stopwords):
    # Remove URLs
    doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
    doc = re.sub(r"www\S+", "", doc, flags=re.MULTILINE)
    # Remove stop words
    if stopwords:
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
def get_token_list(doc, stopwords, doc_name=None):
    # Data cleaning
    doc = preprocess_document(doc, stopwords)

    # Export the preprocessed text
    if doc_name:
        preprocessed_dir = "./../preprocessed"
        makedirs(dirname(join(preprocessed_dir, doc_name + ".txt")), exist_ok=True)
        with open(join(preprocessed_dir, doc_name + ".txt"), 'w') as f:
            f.write(doc)

    return list(tokenize(doc, to_lower=True, deacc = True))

def calculate_tfidf(tfidf_obj, term, cache_file_path=None):
    # Build TF corpus
    tf_corpus = []
    tf_corpus.append(get_text_from_html_file(cache_file_path))
    tf_corpus.append(get_text_from_file(join(INPUT_PATH, term + '.txt')))
    tfidf_obj.update(tf_corpus)
    # features = ctfidf.rank_tfidf(-50, print_=True)
    features = tfidf_obj.filter_tfidf(max=0.001, print_=False)

    # Export into file
    with open(join(STOPWORD_FILE_PATH, 'stopwords_tfidf.txt'), 'w') as f:
        f.write("\n".join(features))

    return features

# Calculate the similarity based on the given word vector
def count_true_positive(doc, keywords, stopwords=False):
    if stopwords:
        tokens = get_token_list(doc, stopwords)
    else:
        tokens = get_token_list(doc, stopwords)
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    token_set = set(lemmatized_tokens)
    str_lemmatized_tokens = " ".join(lemmatized_tokens)
    tp = [[k for k in keyword if k in str_lemmatized_tokens] for keyword in keywords]
    tp = [item for item in tp if item]
    print(tp)
    return len(token_set), len(tp), tp

def calculate_keyword_coverage(term, keywords, stopwords):
    if stopwords:
        # Precompute IDF corpus
        health_topics_path = HEALTH_TOPICS_PATH
        health_topics_files = [f for f in listdir(health_topics_path) if isfile(join(health_topics_path, f))]
        idf_corpus = []
        for file in health_topics_files:
            idf_corpus.append(get_text_from_file(join(health_topics_path, file)))

        ctfidf = CustomizableTfidfVectorizer([], idf_corpus)

        # Run tests over the cache data of SHC websites
        cache_universities = [d for d in listdir(CACHE_DIR_PATH) if isdir(join(CACHE_DIR_PATH, d))]
        for cache_university in cache_universities:
            # Build the path to each university's cache data
            cache_university_path = join(CACHE_DIR_PATH, cache_university)
            cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
            if not cache_files:
                continue

            # Read cache files
            sum_token_stems = 0
            sum_tp_token_stems = 0
            count = 0
            for cache_file in cache_files:
                # Specify the path to each cache file
                cache_file_path = join(cache_university_path, cache_file)
                
                # Calculate TF-IDF
                calculate_tfidf(ctfidf, term, cache_file_path)

                # Calculate similarity between the ideal document and a cached SHC website
                len_token, len_tp_token, tp = count_true_positive(get_text_from_file(join(INPUT_PATH, term + '.txt')), keywords, stopwords)
                sum_token_stems += len_token
                sum_tp_token_stems += len_tp_token
                count += 1

        len_tp_token = sum_token_stems / count
        len_tp_token = sum_tp_token_stems / count
    
    else:
        len_token, len_tp_token, tp = count_true_positive(get_text_from_file(join(INPUT_PATH, term + '.txt')), keywords, stopwords)
                
    print(f'[TP]{len_tp_token} / [TP+FP]{len_token}')
    precision = round(len_tp_token / len_token, 3)
    recall = round(len_tp_token / len(keywords), 3)
    f1 = round((2 * precision * recall) / (precision + recall), 3)
    df = pd.DataFrame(data={
        "Term": [term],
        "Precision": [precision],
        "Recall": [recall],
        "F1-score": [f1],
        "Found Keywords": [tp]
    })
    print(f'Precision: {precision} Recall: {recall} F1-score: {f1}')
    # df.to_csv("Keyword Coverage_" + term + ".csv")


def main():
    if len(sys.argv) > 1:
        term = " ".join(sys.argv[1:])
        with open(join(KEYWORD_DIR_PATH, term + ".txt")) as f:
            calculate_keyword_coverage(term, [[keyword.strip().lower() for keyword in keywords.split(",")] for keywords in f.readlines()], stopwords=False)
    else:
        print("Term is missing.")

if __name__ == "__main__":
    main()