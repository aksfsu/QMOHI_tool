import os
import re
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from keybert import KeyBERT
from keyphrase_vectorizers import KeyphraseCountVectorizer

class KeywordGenerator:
    def __init__(self):
        self.kb = KeyBERT()
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Get text from the text file
    def __get_text_from_file(self, file_path):
        # Open the output file
        with open(file_path, 'r') as f:
            text = f.read()
        return text

    def __preprocess_document(self, doc):
        # Remove URLs
        doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
        doc = re.sub(r"www\S+", "", doc, flags=re.MULTILINE)
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

    def generate_keywords_with_keybert(self, file_path):
        # Read the ideal document for the given term
        doc = self.__get_text_from_file(file_path)
        doc = self.__preprocess_document(doc)

        # Extract keywords
        keywords = [keyword for keyword, _ in self.kb.extract_keywords(doc, keyphrase_ngram_range=(1, 1), stop_words='english', use_mmr=True, diversity=0.7, top_n=1000)]
        keyphrases = [keyword for keyword, _ in self.kb.extract_keywords(doc, vectorizer=KeyphraseCountVectorizer(), use_mmr=True, diversity=0.7, top_n=1000)]
        
        return keywords, keyphrases
