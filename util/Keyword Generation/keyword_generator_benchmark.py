import sys
import re
from os.path import join
from nltk.stem import WordNetLemmatizer
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces, strip_non_alphanum, strip_numeric, strip_punctuation
from gensim.utils import tokenize
from textblob import TextBlob

STOPWORD_FILE_PATH = "./../Ideal Document Generation/stopwords"

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

# Get text from the text file
def get_lines_of_text_from_file(file_path):
    # Open the output file
    with open(file_path, 'r') as f:
        docs = f.readlines()
    return docs

def remove_optional_stopwords(doc):
    doc = list(tokenize(doc, to_lower=True, deacc = True))

    # Read stopword files
    with open(join(STOPWORD_FILE_PATH, "stopwords.txt"), 'r') as f:
        stopwords = f.read()
        doc = [word for word in doc if word not in stopwords]

    return " ".join(doc)

def minimal_preprocess_document(doc):
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

# Preprocess the document
def preprocess_document(doc):
    # Remove URLs
    doc = re.sub(r"http\S+", "", doc, flags=re.MULTILINE)
    doc = re.sub(r"www\S+", "", doc, flags=re.MULTILINE)
    # Remove stop words
    doc = remove_stopwords(doc)
    doc = remove_optional_stopwords(doc)
    # Extract nouns
    blob = TextBlob(doc)
    doc = " ".join(blob.noun_phrases) # This removes keywords like "contraceptive"
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
def get_token_list(doc):
    # Data cleaning
    doc = preprocess_document(doc)
    tokens = list(tokenize(doc, to_lower=True, deacc = True))
    return [WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens]

def main():
    if len(sys.argv) >= 3:
        # Build the search term string from commandline arguments 
        method = str(sys.argv[1])
        term = " ".join([str(sys.argv[i]) for i in range(2, len(sys.argv))])
    else:
        print("Usage: python keyword_generator_benchmark.py [method] [term]")
        exit()

    # --------------------------------------------------------
    #  LDA (gensim)
    # --------------------------------------------------------
    if method == "gensim-lda":
        from gensim.corpora import Dictionary
        from gensim.models import LdaMulticore

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        tokens = [get_token_list(doc)]
        
        bow = Dictionary(tokens)
        bow_corpus = [bow.doc2bow(doc) for doc in tokens]
        lda_model = LdaMulticore(bow_corpus, 
                                num_topics = 1, 
                                id2word = bow,
                                chunksize=2,
                                passes = 1)
        keywords = lda_model.print_topics()

    # --------------------------------------------------------
    #  TF-IDF (Customized Corpora)
    # --------------------------------------------------------
    elif method == "ctfidf":
        from customizable_tfidf_vectorizer import CustomizableTfidfVectorizer

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        ctfidf = CustomizableTfidfVectorizer(docs, docs)
        keywords = ctfidf.filter_tfidf(min=0.02, print_=True)

    # --------------------------------------------------------
    #  TF-IDF (scikit learn)
    # --------------------------------------------------------
    elif method == "sklearn-tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=20)
        vectorizer.fit_transform(docs)
        keywords = vectorizer.get_feature_names_out()

    # --------------------------------------------------------
    #  Word Count (scikit learn)
    # --------------------------------------------------------
    elif method == "sklearn-count":
        from sklearn.feature_extraction.text import CountVectorizer

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        vectorizer = CountVectorizer(ngram_range=(1,2), max_features=20)
        vectorizer.fit_transform(docs)
        keywords = vectorizer.get_feature_names_out()

    # --------------------------------------------------------
    #  LDA (gensim) using TF-IDF
    # --------------------------------------------------------
    elif method == "gensim-lda-tfidf":
        from gensim.corpora import Dictionary
        from gensim.models import TfidfModel, LdaMulticore

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        token_list = [get_token_list(doc) for doc in docs]

        bow = Dictionary(token_list)
        bow_corpus = [bow.doc2bow(doc) for doc in token_list]

        tfidf = TfidfModel(bow_corpus)
        corpus_tfidf = tfidf[bow_corpus]

        lda_model = LdaMulticore(corpus_tfidf, 
                                num_topics = 1, 
                                id2word = bow,
                                chunksize=2,
                                passes = 1)
        keywords = lda_model.print_topics()

    # --------------------------------------------------------
    #  LDA (scikit learn)
    # --------------------------------------------------------
    elif method == "sklearn-lda":
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        count_vector = CountVectorizer()
        doc_term_matrix = count_vector.fit_transform(docs)

        lda = LatentDirichletAllocation(n_components=1, max_iter=10, random_state=42)
        lda.fit(doc_term_matrix)
        topic_tokens_id = lda.components_[0].argsort()[-20:]
        keywords = [count_vector.get_feature_names_out()[id] for id in topic_tokens_id]

    # --------------------------------------------------------
    #  LSA (scikit learn)
    # --------------------------------------------------------
    elif method == "sklearn-lsa":
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import TruncatedSVD

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        count_vector = CountVectorizer()
        doc_term_matrix = count_vector.fit_transform(docs)

        lsa = TruncatedSVD(n_components=1, n_iter=10)
        lsa.fit(doc_term_matrix)

        topic_tokens_id = lsa.components_[0].argsort()[-20:]
        keywords = [count_vector.get_feature_names_out()[id] for id in topic_tokens_id]

    # --------------------------------------------------------
    #  BERTopic
    # --------------------------------------------------------
    elif method == "bertopic":
        from bertopic import BERTopic

        docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        docs = [get_token_list(doc) for doc in docs]
        docs = [" ".join(doc) for doc in docs if len(doc)]

        bertopic_model = BERTopic(nr_topics=10)
        topics, probs = bertopic_model.fit_transform(docs)
        keywords = bertopic_model.get_topic_info()

    # --------------------------------------------------------
    #  Word Cloud
    # --------------------------------------------------------
    elif method == "wordcloud":
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        doc = " ".join(get_token_list(doc))

        wordcloud = WordCloud(width=800, height=800,
                background_color ='white',
                min_font_size=10,
                max_words=20).generate(doc)
 
        # plot the WordCloud image                      
        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.show()

    # --------------------------------------------------------
    #  keyBERT
    # --------------------------------------------------------
    elif method == "keybert":
        from keybert import KeyBERT

        # docs = get_lines_of_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        # docs = [get_token_list(doc) for doc in docs]
        # docs = [" ".join(doc) for doc in docs if len(doc)]
        # doc = ". ".join(docs)
        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        doc = minimal_preprocess_document(doc)
        # doc = " ".join(get_token_list(doc))

        kw_model = KeyBERT()
        keywords = [keyword for keyword, _ in kw_model.extract_keywords(doc, keyphrase_ngram_range=(1, 1), use_mmr=True, diversity=0.2, top_n=40)]

    # --------------------------------------------------------
    #  Rake
    # --------------------------------------------------------
    elif method == "rake":
        from multi_rake import Rake

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        doc = minimal_preprocess_document(doc)

        rake = Rake(language_code="en", max_words=2, generated_stopwords_max_len=30, generated_stopwords_min_freq=1)
        keywords = [keyword for keyword, _ in rake.apply(doc)[:10]]

    # --------------------------------------------------------
    #  yake
    # --------------------------------------------------------
    elif method == "yake":
        import yake

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        tokens = get_token_list(doc)
        doc = " ".join([WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens])
        # doc = minimal_preprocess_document(doc)

        yake_ke = yake.KeywordExtractor(lan="en", n=1, top=10, features=None)
        keywords = [keyword for keyword, _ in yake_ke.extract_keywords(doc)[:10]]

    # --------------------------------------------------------
    #  yake (pke)
    # --------------------------------------------------------
    elif method == "pke-yake":
        from pke.unsupervised import YAKE
        from pke.lang import stopwords

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        tokens = get_token_list(doc)
        doc = " ".join([WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens])
        # doc = minimal_preprocess_document(doc)

        # initialize keyphrase extraction model, here TopicRank
        yake = YAKE()
        yake.load_document(input=doc, language='en', stoplist=stopwords.get('english'), normalization=None)
        yake.candidate_selection(n=2)
        yake.candidate_weighting(window=2, use_stems=False)

        # 10 highest scored candidates
        keywords = [keyword for keyword, _ in yake.get_n_best(n=20)]

    # --------------------------------------------------------
    #  TextRank (pke)
    # --------------------------------------------------------
    elif method == "pke-tr":
        from pke.unsupervised import TopicRank
        from pke.lang import stopwords

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        # tokens = get_token_list(doc)
        # doc = " ".join([WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens])
        doc = minimal_preprocess_document(doc)

        # initialize keyphrase extraction model, here TopicRank
        rank = TopicRank()
        rank.load_document(input=doc, language='en', stoplist=stopwords.get('english'), normalization=None)
        rank.candidate_selection()
        rank.candidate_weighting()

        # 10 highest scored candidates
        keywords = [keyword for keyword, _ in rank.get_n_best(n=10)]

    # --------------------------------------------------------
    #  PositionRank (pke)
    # --------------------------------------------------------
    elif method == "pke-pr":
        from pke.unsupervised import PositionRank
        from pke.lang import stopwords

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        tokens = get_token_list(doc)
        doc = " ".join([WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens])
        # doc = minimal_preprocess_document(doc)

        # initialize keyphrase extraction model, here TopicRank
        rank = PositionRank()
        rank.load_document(input=doc, language='en', stoplist=stopwords.get('english'), normalization=None)
        rank.candidate_selection(maximum_word_number=1)
        rank.candidate_weighting(window=1)

        # 10 highest scored candidates
        keywords = [keyword for keyword, _ in rank.get_n_best(n=10)]

    # --------------------------------------------------------
    #  MultipartiteRank (pke)
    # --------------------------------------------------------
    elif method == "pke-mr":
        from pke.unsupervised import MultipartiteRank
        from pke.lang import stopwords

        doc = get_text_from_file("./../Ideal Document Generation/output/" + term + ".txt")
        # tokens = get_token_list(doc)
        # doc = " ".join([WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens])
        doc = minimal_preprocess_document(doc)
        
        # initialize keyphrase extraction model, here TopicRank
        rank = MultipartiteRank()
        rank.load_document(input=doc, language='en', stoplist=stopwords.get('english'), normalization=None)
        rank.candidate_selection()
        rank.candidate_weighting(alpha=1.1, threshold=0.74, method='average')

        # 10 highest scored candidates
        keywords = [keyword for keyword, _ in rank.get_n_best(n=40)]

    # Output extracted keywords
    print(keywords)

if __name__ == "__main__":
    main()