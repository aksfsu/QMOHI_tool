import re
from collections import Counter
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize

class Summarizer():
    def __init__(self, doc, keywords=[], keyweight=2):
        self.sentences = sent_tokenize(doc)
        self.keywords = [w.lower() for w in keywords]
        self.keyword_weight = keyweight
        self.token_counter = Counter(self.__get_token_list(doc))
        self.sentence_scores = self.__rank_sentences()

    # Preprocess the document
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

    # Tokenize the document
    def __get_token_list(self, doc):
        doc = self.__preprocess_document(doc)
        return [PorterStemmer().stem(token.lower()) for token in word_tokenize(doc)]

    def __rank_sentences(self):
        sentence_scores = Counter()
        for sentence in self.sentences:
            for word, freq in self.token_counter.items():
                if word in self.keywords:
                    sentence_scores[sentence] += freq * self.keyword_weight
                elif word in sentence.lower():
                    sentence_scores[sentence] += freq
        return sentence_scores
    
    def summarize(self, n=0, weight=1.2):
        summary = ""
        if n > 0:
            for sentence in self.sentences:
                if sentence in [s[0] for s in self.sentence_scores.most_common(n)]:
                    summary += " " + sentence
        else:
            average = sum(self.sentence_scores.values()) / len(self.sentence_scores)
            for sentence in self.sentences:
                if (sentence in self.sentence_scores) and (self.sentence_scores[sentence] > (weight * average)):
                    summary += " " + sentence
        return summary[1:]
