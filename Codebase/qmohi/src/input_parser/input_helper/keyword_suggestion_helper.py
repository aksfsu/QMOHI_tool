import os
from os.path import join, dirname
from qmohi.src.input_parser.input_helper.ideal_document_generator import generate_ideal_document
from qmohi.src.input_parser.input_helper.keyword_generator import KeywordGenerator

NUM_SUGGESTIONS = 10
COMPARISON_DOCUMENT_PATH = "./"

def get_topic(query):
    idx = query.find(" OR ")
    if idx == -1:
        return query
    return query[:idx]

def suggest_keywords(api_keys, cse_id, keywords, ideal_doc_path):
    iteration = True
    kg = KeywordGenerator()
    suggested_keywords = set(keywords)

    while iteration:
        # Generate comparison document
        print("\nGenerating keywords...")
        output_file_path = join(dirname(ideal_doc_path), get_topic(keywords[0]) + ".txt")
        generate_ideal_document(output_file_path, api_keys, cse_id, depth=1, keywords=keywords)

        # Extract keywords
        unigram_keywords, bigram_keywords = kg.generate_keywords_with_keybert(output_file_path)

        # Collect new keywords
        unigram_suggestions = []
        for keyword in unigram_keywords:
            if keyword not in suggested_keywords:
                unigram_suggestions.append(keyword)
                suggested_keywords.add(keyword)
            if len(unigram_suggestions) == NUM_SUGGESTIONS:
                break

        bigram_suggestions = []
        for keyword in bigram_keywords:
            if keyword not in suggested_keywords:
                bigram_suggestions.append(keyword)
                suggested_keywords.add(keyword)
            if len(bigram_suggestions) == NUM_SUGGESTIONS:
                break

        # Let users select keywords to add
        print(f"\nCurrent Keywords: ", end="")
        for i, keyword in enumerate(keywords):
            if i == len(keywords) - 1:
                print(keyword)
            else:
                print(f"{keyword}, ", end="")
        keyword_suggestions = unigram_suggestions + bigram_suggestions
        print(f"\nHere Are the Suggested Keywords:")
        for i, keyword in enumerate(keyword_suggestions):
            print(f"{i + 1}: {keyword} ")

        print("\nPlease enter the indices of the above suggested keywords you would like to add.")
        print('Please separate each number with ",".')
        print("You can skip this step by pressing enter.")
        indices = input(f"Keyword Indices to Add: ")
        if indices:
            indices = indices.split(",")
            indices = [index.strip() for index in indices]
            indices = [int(index) - 1 for index in indices if index.isnumeric() and int(index) > 0 and int(index) <= len(keyword_suggestions)]
            keywords.extend([keyword_suggestions[index] for index in indices])

        while True:
            cont = input(f"Would you like QMOHI to suggest more keywords? (Y/n) : ")
            if cont.lower() in ["y", "yes"]:
                break
            elif cont.lower() in ["n", "no"]:
                iteration = False
                print(f"\nCurrent Keywords: ", end="")
                for i, keyword in enumerate(keywords):
                    if i == len(keywords) - 1:
                        print(keyword)
                    else:
                        print(f"{keyword}, ", end="")
                break

    return keywords
