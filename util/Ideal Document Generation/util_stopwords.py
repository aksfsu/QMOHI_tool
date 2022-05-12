'''
Script to concatenate lists of stop words in separate files
and export into a single file "stopwords.txt"
'''

from os.path import exists, join

STOPWORD_FILE_PATH = "./stopwords"

FILE_PATH_LIST = [
    "stopwords.txt", #fixed
    # Add stop words files below to remove overlaps
    "long_stop_words.txt",
    "clinical_stop_words.txt",
    "medical_stop_words.txt",
    "health_topics_high_idf_words.txt"
]

if not exists(join(STOPWORD_FILE_PATH, FILE_PATH_LIST[0])):
    open(join(STOPWORD_FILE_PATH, FILE_PATH_LIST[0]), 'w').close()

vocab = set()
for file_path in FILE_PATH_LIST:
    with open(join(STOPWORD_FILE_PATH, file_path), 'r') as f:
        vocab.update(set(f.readlines()))

with open(join(STOPWORD_FILE_PATH, FILE_PATH_LIST[0]), 'w') as f:
    f.writelines(list(vocab))
