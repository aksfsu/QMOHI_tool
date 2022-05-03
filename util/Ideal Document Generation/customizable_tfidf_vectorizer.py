from math import isnan
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname, exists
import pandas as pd
import numpy as np
from gensim.corpora import Dictionary
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize
from bs4 import BeautifulSoup
import re

class CustomizableTfidfVectorizer:
    def __init__(self, tf_docs, idf_docs=[], idf_dir=""):
        self.tf_docs = tf_docs
        # If the directory path is provided, calculate IDF
        # using the documents in the directory. Otherwise,
        # a list of token lists must be passed.
        if idf_dir:
            self.idf_dct = self.__precompute_idf(idf_dir)
        else:
            self.idf_dct = self.__get_token_dict(idf_docs)
        self.tfidf = self.__compute_tfidf()
        self.vocab = list(set(key[1] for key in self.tfidf.keys()))
        self.tfidf_vec = self.__vectorize_tfidf()

    # Preprocess the document
    def __preprocess_document(self, doc):
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
    def __get_token_list(self, doc):
        # Data cleaning
        doc = self.__preprocess_document(doc)
        return list(tokenize(doc, to_lower=True, deacc = True))

    # Get tokens in Gensim Dictionary instance
    def __get_token_dict(self, docs):
        token_list = [self.__get_token_list(doc) for doc in docs]
        return Dictionary(token_list)

    # Compute Inverse Document Frequency using the given list of token lists
    def __idf(self, word):
        return np.log((self.idf_dct.num_docs + 1)/(self.idf_dct.dfs[self.idf_dct.token2id.get(word)] + 1)) + 1

    # Compute Inverse Document Frequency using the documents in the directory
    def __precompute_idf(self, idf_dir):
        idf_dct = Dictionary()
        idf_docs = [join(idf_dir, f) for f in listdir(idf_dir) if isfile(join(idf_dir, f))]
        if not idf_docs:
            return {}
        for idf_doc in idf_docs:
            with open(idf_doc, "r") as file:
                doc = file.read()
                token_list = self.__get_token_list(doc)
                idf_dct.add_documents([token_list])
        return idf_dct

    # Caltulate TF-IDF and return the Gensim Dictionary object
    def __compute_tfidf(self):
        tfidf = {}
        for doc_idx, doc in enumerate(self.tf_docs):
            tf_dct = self.__get_token_dict([doc])
            for word in tf_dct.itervalues():
                if self.idf_dct.token2id.get(word):
                    tf = tf_dct.cfs[tf_dct.token2id.get(word)] / len(doc)
                    tfidf[doc_idx, word] = tf * self.__idf(word)
        return tfidf

    # Vectorize the TF-IDF dictionary
    def __vectorize_tfidf(self):
        tfidf_vec = np.zeros((len(self.tf_docs), len(self.vocab)))
        for k, v in self.tfidf.items():
            tfidf_vec[k[0]][self.vocab.index(k[1])] = v
        # print(tfidf_vec)
        return tfidf_vec

    # Get the document by ID
    def id2doc(self, idx):
        return self.tf_docs[idx]

    # Get the token by ID
    def id2token(self, idx):
        return self.vocab[idx]

    # Get the vocabulary
    def feature_names(self):
        return self.vocab

    # Get the number of documents
    def idf_doc_num(self):
        return self.idf_dct.num_docs

    # Get the most common words in IDF documents
    def most_common_idf(self, n=None):
        return self.idf_dct.most_common(n)

    # Get the TF-IDF vector
    def tfidf_vec(self):
        return self.tfidf_vec

    # Rank words by TD-IDF values and return a set of top 'n' words in each document
    def rank_tfidf(self, n=5, printout=None):
        # Convert the TF-IDF dictionary to a pandas dataframe
        tfidf_df = pd.DataFrame(columns=['doc_id'] + self.vocab)
        tfidf_df.set_index("doc_id", inplace = True)
        tfidf_df['doc_id'] = [i for i in range(len(self.tf_docs))]
        for k, v in self.tfidf.items():
            tfidf_df.loc[tfidf_df.doc_id[k[0]], k[1]] = v

        # Sort words in each document by their TF-IDF values
        tfidf_lst = []
        for i in range(len(self.tf_docs)):
            dct = tfidf_df.loc[tfidf_df.doc_id[i], tfidf_df.columns!='doc_id'].to_dict()
            cleaned_dct = {}
            for k, v in dct.items():
                if not isnan(v):
                    cleaned_dct[k] = v
            tfidf_lst.append(cleaned_dct)

        # Show top 'n' words in each document
        features = set()
        if printout:
            print(f' doc_id | token | TF-IDF ')
            print('---------------------------')
        for doc_id, tfidf_dct in enumerate(tfidf_lst):
            sorted_dct = dict(sorted(tfidf_dct.items(), key=lambda x:x[1], reverse=(n>0)))
            for i, (k, v) in enumerate(sorted_dct.items()):
                if i >= abs(n):
                    break
                if printout:
                    print(f' {doc_id} | {k} \t| {v} ')
                features.add(k)

        return features

def test():
    # Toy corpora
    tf_docs = [
        "It is the measure of the frequency of words in a document.",
        "It is the ratio of the number of times the word appears in a document compared to the total number of words in that document."
    ]

    idf_docs = [
        "The words that occur rarely in the corpus have a high IDF score.",
        
        "It is the log of the ratio of the number of documents to the number of documents containing the word.",

        "We take log of this ratio because when the corpus becomes large IDF values can get large causing it to explode hence taking log will dampen this effect.",

        "we cannot divide by 0, we smoothen the value by adding 1 to the denominator."
    ]

    # Test script
    '''
    ctfidf = CustomizableTfidfVectorizer(tf_docs, idf_docs)
    ctfidf.tfidf_vec()
    # print(ctfidf.id2doc(0))
    # print(ctfidf.id2token(2))
    ctfidf.rank_tfidf(5)
    '''
    ctfidf = CustomizableTfidfVectorizer(tf_docs, idf_dir="./health_topics_summary")
    print(ctfidf.idf_doc_num)
    print(ctfidf.most_common_idf(50))
    print(ctfidf.rank_tfidf(10))

# Run the test
test()