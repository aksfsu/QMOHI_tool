import sys
import os
import re
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric
from gensim.utils import tokenize

from keybert import KeyBERT

# from pke.unsupervised import MultipartiteRank
# from pke.lang import stopwords

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

class KeywordGenerator:
    def __init__(self):
        self.kb = KeyBERT()
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        return

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
        unigram_keywords = [keyword for keyword, _ in self.kb.extract_keywords(doc, keyphrase_ngram_range=(1, 1), stop_words='english', use_mmr=True, diversity=0.4, top_n=1000)]
        bigram_keywords = [keyword for keyword, _ in self.kb.extract_keywords(doc, keyphrase_ngram_range=(1, 2), stop_words='english', use_mmr=True, diversity=0.4, top_n=1000)]

        # Extract a set of unique tokens
        # tokens = [list(tokenize(keyword, to_lower=True, deacc = True)) for keyword in keywords]
        # keywords = set(sum(tokens, []))
        return unigram_keywords, bigram_keywords

    '''
    def generate_keywords_with_multipartilerank(self, file_path):
        doc = self.__get_text_from_file(file_path)
        doc = self.__preprocess_document(doc)
        
        # initialize keyphrase extraction model, here TopicRank
        rank = MultipartiteRank()
        rank.load_document(input=doc, language='en', stoplist=stopwords.get('english'), normalization=None)
        rank.candidate_selection()
        rank.candidate_weighting(alpha=1.1, threshold=0.7, method='average')

        # Extract a set of unique tokens
        tokens = [list(tokenize(keyword, to_lower=True, deacc = True)) for keyword, _ in rank.get_n_best(n=40)]
        keywords = set(sum(tokens, []))
        return keywords
    '''


'''
# Unit test
def main():
    if len(sys.argv) >= 2:
        terms = [" ".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])]
    else:
        terms = EXPERIMENTAL_TERMS

    kg = KeywordGenerator()
    for term in terms:
        keywords = kg.generate_keywords_with_keybert("./../Ideal Document Generation/output/" + term + ".txt")
        print(f'--- Keywords for {term} ({len(keywords)}) ---\n{keywords}')

if __name__ == "__main__":
    main()
'''