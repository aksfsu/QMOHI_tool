import re
import numpy as np
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from gensim.parsing.preprocessing import strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize
from nltk.stem import WordNetLemmatizer

from qmohi.src.metric_calc.customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

STOPWORD_FILE_PATH = "./qmohi/src/metric_calc/stopwords"
HEALTH_TOPICS_CORPUS_PATH = "./qmohi/src/metric_calc/medlineplus_health_topics_corpus.txt"

class Similarity:
    def __init__(self, word_vector, keywords=[], weight=1):
        print("Loading model...")
        self.word_vector = word_vector
        print("Loaded")
        lemmatizer = WordNetLemmatizer()
        self.keywords = [lemmatizer.lemmatize(keyword) for keyword in keywords]
        self.weight = weight

    def remove_stopwords(self, doc):
        stopword_file_paths = [join(STOPWORD_FILE_PATH, f) for f in listdir(STOPWORD_FILE_PATH) if isfile(join(STOPWORD_FILE_PATH, f)) and f.startswith("stopwords")]
        doc = list(tokenize(doc, to_lower=True, deacc = True))
        # Read stopword files
        for stopword_file_path in stopword_file_paths:
            with open(stopword_file_path, 'r') as f:
                stopwords = f.read()
                doc = [word for word in doc if word not in stopwords]
        return " ".join(doc)

    # Preprocess the document
    def preprocess_document(self, doc):
        # Remove URLs
        doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
        doc = re.sub(r"www\S+", "", doc, flags=re.MULTILINE)
        # Remove stop words
        doc = self.remove_stopwords(doc)
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
    def get_token_list(self, doc, _print=False):
        # Data cleaning
        doc = self.preprocess_document(doc)
        if _print:
            print(doc)
        # Return token list
        return list(tokenize(doc, to_lower=True, deacc = True))

    def calculate_tfidf(self, ideal_document, shc_content):
        # Precompute IDF corpus
        with open(HEALTH_TOPICS_CORPUS_PATH, "r") as f:
            idf_corpus = f.readlines()

        # Build TF corpus
        tf_corpus = [ideal_document, shc_content]

        ctfidf = CustomizableTfidfVectorizer(tf_corpus, idf_corpus)

        features = ctfidf.filter_tfidf(max=0.001, print_=False)

        # Export into file
        with open(join(STOPWORD_FILE_PATH, 'stopwords_tfidf.txt'), 'w') as f:
            f.write("\n".join(features))

        return features

    def get_label(self, similarity):
        if similarity >= 0.7:
            return "High"
        if similarity >= 0.6:
            return "Moderate"
        return "Low"

    # Calculate the similarity based on the given word vector
    def calculate_similarity(self, ideal_document, shc_content):
        # Calculate TF-IDF
        self.calculate_tfidf(ideal_document, shc_content)

        # sum1 will hold the sum of all of its word's vectors
        sum1 = [0] * len(self.word_vector['word'])
        for token in self.get_token_list(ideal_document):
            if token in self.word_vector:
                if token in self.keywords:
                    w = self.weight
                else:
                    w = 1
                sum1 = np.sum([sum1, self.word_vector[token] * w], axis=0)

        # sum2 will hold the sum of all of its word's vectors
        sum2 = [0] * len(self.word_vector['word'])
        for token in self.get_token_list(shc_content):
            if token in self.word_vector:
                if token in self.keywords:
                    w = self.weight
                else:
                    w = 1
                sum2 = np.sum([sum2, self.word_vector[token] * w], axis=0)

        # Calculate the cosine similarity
        similarity = cosine_similarity([sum1], [sum2])[0][0]
        return similarity, self.get_label(similarity)
