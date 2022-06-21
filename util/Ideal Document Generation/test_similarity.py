import re
import numpy as np
import pandas as pd
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname, exists
import csv
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize

from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

import seaborn as sns
import matplotlib.pyplot as plt

WORD_VECTOR_PATH = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/GoogleNews-vectors-negative300.bin"
STOPWORD_FILE_PATH = "./stopwords"

EXPERIMENTAL_TERMS = [
    "Medicated Abortion",
    "Abortion",
    "Accidental Injury", #
    "Broken Limbs",
    "First Aid", #
    "Allergy", #
    "Asthma",
    "Flu",
    "Cold", #
    "Standard Immunizations",
    "Vaccines", #
    "Tobacco",
    "Alcohol",
    "Drug Issues",
    "Mental Health Depression",
    "Anxiety",
    "Stress",
    "Time Management",
    "Sexual Harrassment",
    "Abuse",
    "Assault",
    "Violence",
    "Body Image",
    "Nutrition",
    "Obesity",
    "HIV",
    "STD",
    "Sexual Health",
    "Safe Sex",
    "Urinary Tract Infections",
]

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
    doc = re.sub(r"www\S+", "", doc, flags=re.MULTILINE)
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

    # Export the preprocessed text
    if doc_name:
        preprocessed_dir = "./preprocessed"
        makedirs(dirname(join(preprocessed_dir, doc_name + ".txt")), exist_ok=True)
        with open(join(preprocessed_dir, doc_name + ".txt"), 'w') as f:
            f.write(doc)

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

def calculate_tfidf(tfidf_obj, term, cache_file_path=None):
    # Build TF corpus
    tf_corpus = []
    tf_corpus.append(get_text_from_html_file(cache_file_path))
    tf_corpus.append(get_text_from_file(join("./output", term + '.txt')))
    tfidf_obj.update(tf_corpus)
    # features = ctfidf.rank_tfidf(-50, print_=True)
    features = tfidf_obj.filter_tfidf(max=0.001, print_=False)

    # Export into file
    with open(join(STOPWORD_FILE_PATH, 'stopwords_tfidf.txt'), 'w') as f:
        f.write("\n".join(features))

    return features

def main():
    # Load the word vector
    print("Loading model...")
    word_vector = KeyedVectors.load_word2vec_format(WORD_VECTOR_PATH, binary=True)
    print("Loaded")

    # Create a dataframe for visualization
    results_df = pd.DataFrame(columns=['Website', 'Term', 'Similarity'])

    # Precompute IDF corpus
    health_topics_path = "./health_topics_summary"
    health_topics_files = [f for f in listdir(health_topics_path) if isfile(join(health_topics_path, f))]
    idf_corpus = []
    for file in health_topics_files:
        idf_corpus.append(get_text_from_file(join(health_topics_path, file)))

    ctfidf = CustomizableTfidfVectorizer([], idf_corpus)
    
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
                
                # Calculate TF-IDF
                calculate_tfidf(ctfidf, term, cache_file_path)
                
                # Calculate similarity between the ideal document and a cached SHC website
                similarity = calculate_similarity(word_vector, 
                    get_text_from_file(join("./output", term + '.txt')), 
                    get_text_from_html_file(cache_file_path),
                    term,
                    cache_university + "-" + cache_file
                )
                csv_writer.writerow([cache_university, cache_file, similarity])
                # print(f'{cache_university}/{cache_file}: {round(similarity * 100, 3)}% ({similarity})')
                
                similarity_data = {
                    'Website': [cache_university + ' ' + cache_file],
                    'Term': [term],
                    'Similarity': [similarity]
                }
                
                results_df = pd.concat([results_df, pd.DataFrame(similarity_data)], ignore_index=True)

    output_file.close()
    # print(results_df.head())

    # Visualize the results
    results_df = results_df.groupby(['Term'], sort=False).apply(lambda x: x.sort_values(['Similarity'], ascending=False)).reset_index(drop=True)
    results_df.reset_index(drop=True, inplace=True)
    f, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
    g = sns.lineplot(data=results_df, x="Website", y="Similarity", hue="Term")
    plt.xticks(rotation=50, horizontalalignment='right')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.title("Similarity")
    plt.show()

    return

if __name__ == "__main__":
    main()