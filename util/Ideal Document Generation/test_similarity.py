import re
import numpy as np
import pandas as pd
import sys
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
import csv
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors
from gensim.parsing.preprocessing import strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize

from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

import seaborn as sns
import matplotlib.pyplot as plt

WORD_VECTOR_PATH = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/GoogleNews-vectors-negative300.bin"
STOPWORD_FILE_PATH = "./stopwords"

EXPERIMENTAL_TERMS = [
    "Medicated Abortion",
    "Abortion",
    "Accidental Injury",
    "Broken Limbs",
    "First Aid",
    "Allergy",
    "Asthma",
    "Flu",
    "Cold",
    "Standard Immunizations",
    "Vaccines",
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

MEDICATED_ABORTION_KEYWORDS = [
    "nonsurgical", "abortion",
    "surgical",
    "medical",
    "medicated",
    "medication",
    "medications",
    "mifepristone",
    "misoprostol",
    "mifeprex",
    "ru",
    "pill",
    "pills"
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
def calculate_similarity(word_vector, keywords, weight, doc1, doc2, doc_name1=None, doc_name2=None):
    # sum1 will hold the sum of all of its word's vectors
    sum1 = [0] * len(word_vector['word'])
    for token in get_token_list(doc1, doc_name1):
        if token in word_vector:
            if token in keywords:
                w = weight
            else:
                w = 1
            sum1 = np.sum([sum1, word_vector[token] * w], axis=0)

    # sum2 will hold the sum of all of its word's vectors
    sum2 = [0] * len(word_vector['word'])
    for token in get_token_list(doc2, doc_name2):
        if token in word_vector:
            if token in keywords:
                w = weight
            else:
                w = 1
            sum2 = np.sum([sum2, word_vector[token] * w], axis=0)

    # Calculate the cosine similarity
    similarity = cosine_similarity([sum1], [sum2])
    return similarity[0][0]

def calculate_tfidf(tfidf_obj, ideal_document_content, cache_file_content):
    # Build TF corpus
    tf_corpus = []
    tf_corpus.append(cache_file_content)
    tf_corpus.append(ideal_document_content)
    tfidf_obj.update(tf_corpus)
    # features = ctfidf.rank_tfidf(-50, print_=True)
    features = tfidf_obj.filter_tfidf(max=0.0008, print_=False)

    # Export into file
    with open(join(STOPWORD_FILE_PATH, 'stopwords_tfidf.txt'), 'w') as f:
        f.write("\n".join(features))

    return features

def get_label(similarity):
    if similarity >= 0.7:
        return "High"
    if similarity >= 0.6:
        return "Moderate"
    return "Low"

def evaluate_similarity(word_vector, ideal_document_path, output_file_path):
    # Precompute IDF corpus
    health_topics_path = "./health_topics_summary"
    health_topics_files = [f for f in listdir(health_topics_path) if isfile(join(health_topics_path, f))]
    idf_corpus = []
    for file in health_topics_files:
        idf_corpus.append(get_text_from_file(join(health_topics_path, file)))

    ctfidf = CustomizableTfidfVectorizer([], idf_corpus)

    # Create a dataframe to export the result
    results_df = pd.DataFrame(columns=['University', 'Similarity', 'Label'])

    ideal_document_content = get_text_from_file(ideal_document_path)

    # Run tests over the cache data of SHC websites
    cache_dir_path = "./../../Codebase/QMOHI_input/experiments/2021/QMOHI_input_11thOct2021/output/Output 2022-08-08 16:23:21 Medical Abortion/saved_webpages"
    cache_universities = [d for d in listdir(cache_dir_path) if isdir(join(cache_dir_path, d))]
    for cache_university in cache_universities:
        # Build the path to each university's cache data
        cache_university_path = join(cache_dir_path, cache_university)
        cache_files = [f for f in listdir(cache_university_path) if isfile(join(cache_university_path, f))]
        if not cache_files:
            continue

        # Collect cache file content
        cache_file_content = ""
        for cache_file in cache_files:
            cache_file_content += " " + get_text_from_html_file(join(cache_university_path, cache_file))
                
        # Calculate TF-IDF
        calculate_tfidf(ctfidf, ideal_document_content, cache_file_content)
        
        # Calculate similarity between the ideal document and a cached SHC website
        similarity = calculate_similarity(word_vector, 
            keywords=[],
            weight=1,
            doc1=ideal_document_content, 
            doc2=cache_file_content
        )
        # print(f'{cache_university}/{cache_file}: {round(similarity * 100, 3)}% ({similarity})')

        similarity_data = {
            'University': [cache_university],
            'Similarity': [similarity],
            'Label': [get_label(similarity)]
        }
        
        results_df = pd.concat([results_df, pd.DataFrame(similarity_data)], ignore_index=True)

    makedirs(dirname(output_file_path), exist_ok=True)
    results_df.to_csv(output_file_path)
    # print(results_df.head())
    return results_df


def main():
    # Load the word vector
    print("Loading model...")
    word_vector = KeyedVectors.load_word2vec_format(WORD_VECTOR_PATH, binary=True)
    print("Loaded")

    # Build the search term string from commandline arguments 
    if len(sys.argv) > 1:
        term = " ".join(sys.argv[1:])
        ideal_document_path = join("./output", term + ".txt")
        output_file_path = "./similarity_" + term + ".csv"
        evaluate_similarity(word_vector, ideal_document_path, output_file_path)
    
    else:
        results_df = pd.DataFrame(columns=['University', 'Similarity', 'Term'])
        for term in EXPERIMENTAL_TERMS:
            ideal_document_path = join("./output", term + ".txt")
            output_file_path = "./similarity_" + term + ".csv"
            result_df = evaluate_similarity(word_vector, ideal_document_path, output_file_path)
            result_df.drop(columns='Label', inplace=True)
            result_df['Term'] = [term] * result_df.shape[0]
            results_df = pd.concat([results_df, result_df], ignore_index=True)

        # Visualize the results
        results_df = results_df.groupby(['Term'], sort=False).apply(lambda x: x.sort_values(['Similarity'], ascending=False)).reset_index(drop=True)
        f, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
        g = sns.lineplot(data=results_df, x='University', y='Similarity', hue='Term')
        plt.xticks(rotation=50, horizontalalignment='right')
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        plt.title("Similarity")
        plt.show()


if __name__ == "__main__":
    main()
