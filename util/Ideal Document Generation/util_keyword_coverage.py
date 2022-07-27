import re
from os import listdir, makedirs
from os.path import isdir, isfile, join, dirname
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize
from gensim.parsing.porter import PorterStemmer

from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer
from util_text_summarizer import Summarizer

INPUT_PATH = "./summarized"
STOPWORD_FILE_PATH = "./stopwords"

CONTRACEPTION_KEYWORDS = [
    "birth",
    "control",
    "iud",
    "iuds",
    "progesterone",
    "progestin",
    "hormonal",
    "mirena",
    "skyla",
    "kyleena",
    "liletta",
    "copper",
    "paragard",
    "implant",
    "implants",
    "nexplanon",
    "injection",
    "injections",
    "shot",
    "shots",
    "depo-provera",
    "depo",
    "emergency",
    "contraception",
    "contraceptive",
    "morning",
    "b",
    "levonorgestrel",
    "ella",
    "ulipristal",
    "acetate",
    "pill",
    "pills",
    "diaphragm",
    "spermicide",
    "spermicides",
    "patch",
    "patches",
    "vaginal",
    "ring",
    "rings",
    "cervical", 
    "cap",
    "caps",
]

LARC_KEYWORDS = [
    "iud",
    "iuds",
    "progesterone",
    "progestin",
    "hormonal",
    "mirena",
    "skyla",
    "kyleena",
    "liletta",
    "copper",
    "non-hormonal",
    "paragard",
    "contraceptive",
    "implant",
    "implants",
    "nexplanon",
    "injection",
    "injections",
    "shot",
    "shots",
    "depo-provera",
    "depo",
]

# === Test Settings ====================
TERM = "Long Acting Reversible Contraception"
KEYWORDS = LARC_KEYWORDS
# ======================================

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

    # Read stopword files
    for stopword_file_path in stopword_file_paths:
        with open(stopword_file_path, 'r') as f:
            stopwords = f.read()
            doc = [word for word in doc if word not in stopwords]
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
    # Summarize
    doc = Summarizer(doc, KEYWORDS).summarize()
    with open(join("./summarized", TERM + ".txt"), 'w') as f:
        f.write(doc)

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
def count_true_positive(doc):
    tokens = get_token_list(doc)
    token_set = set(tokens)
    token_stems = PorterStemmer().stem_documents(token_set)
    token_stems_set = set(token_stems)
    tps = [token for token in token_set if token in KEYWORDS]
    tp_token_stems = PorterStemmer().stem_documents(tps)
    tp_token_stems_set = set(tp_token_stems)
    return (len(token_stems_set), len(tp_token_stems_set))

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

def main():
    # Precompute IDF corpus
    health_topics_path = "./health_topics_summary"
    health_topics_files = [f for f in listdir(health_topics_path) if isfile(join(health_topics_path, f))]
    idf_corpus = []
    for file in health_topics_files:
        idf_corpus.append(get_text_from_file(join(health_topics_path, file)))

    ctfidf = CustomizableTfidfVectorizer([], idf_corpus)

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
        sum_token_stems = 0
        sum_tp_token_stems = 0
        count = 0
        for cache_file in cache_files:
            # Specify the path to each cache file
            cache_file_path = join(cache_university_path, cache_file)
            
            # Calculate TF-IDF
            calculate_tfidf(ctfidf, TERM, cache_file_path)

            # Calculate similarity between the ideal document and a cached SHC website
            len_token_stems, len_tp_token_stems = count_true_positive(get_text_from_file(join(INPUT_PATH, TERM + '.txt')))
            sum_token_stems += len_token_stems
            sum_tp_token_stems += len_tp_token_stems
            count += 1

    sum_token_stems /= count
    sum_tp_token_stems /= count
    print(f'[TP]{sum_tp_token_stems} / [TP+FP]{sum_token_stems}')

if __name__ == "__main__":
    main()