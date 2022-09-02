import os
from os.path import join
from qmohi.src.input_parser.input_helper.ideal_document_generator import generate_ideal_document
from qmohi.src.input_parser.input_helper.keyword_generator import KeywordGenerator

NUM_SUGGESTIONS = 10

def get_topic(query):
    idx = query.find(" OR ")
    if idx == -1:
        return query
    return query[:idx]

def suggest_keywords(api_keys, cse_id, keywords):
    first_time = True
    iteration = True
    kg = KeywordGenerator()
    unigram_suggested = set()
    bigram_suggested = set()

    while iteration:
        if not first_time:
            keywords = []
        
            print("""
Accuracy can be improved by providing the full form of the word in a short form by inputting "KW OR Keyword" 
(Putting " OR " between short form and long form).
Press return key to end input and continue to the next step.
            """)

            i = 1
            while True:
                term = input(f"Keyword {i} : ")
                if not term:
                    break
                keywords.append(term)
                i += 1
        
        first_time = False

        print("\nGenerating keywords...")
        output_file_path = join("./", get_topic(keywords[0]) + ".txt")
        generate_ideal_document(output_file_path, api_keys, cse_id, keywords)

        unigram_keywords, bigram_keywords = kg.generate_keywords_with_keybert(output_file_path)

        os.remove(output_file_path)

        unigram_suggestions = []
        for keyword in unigram_keywords:
            if keyword not in unigram_suggested:
                unigram_suggestions.append(keyword)
                unigram_suggested.add(keyword)
            if len(unigram_suggestions) == NUM_SUGGESTIONS:
                break

        bigram_suggestions = []
        for keyword in bigram_keywords:
            if keyword not in bigram_suggested:
                bigram_suggestions.append(keyword)
                bigram_suggested.add(keyword)
            if len(bigram_suggestions) == NUM_SUGGESTIONS:
                break

        print(f"\nKeyword Suggestion:\n{unigram_suggestions}\n{bigram_suggestions}")

        while True:
            cont = input(f"Continue to next iteration? (Y/n) : ")
            if cont.lower() in ["y", "yes"]:
                break
            elif cont.lower() in ["n", "no"]:
                iteration = False
                break

    return keywords
