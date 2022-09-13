import os
from os.path import join, dirname
from qmohi.src.input_parser.input_helper.ideal_document_generator import generate_ideal_document
from qmohi.src.input_parser.input_helper.keyword_generator import KeywordGenerator

NUM_SUGGESTIONS = 10
COMPARISON_DOCUMENT_PATH = "./"


class KeywordSuggestionHelper:
    def __init__(self, api_keys, cse_id, ideal_doc_path, keywords, num_of_suggestions=NUM_SUGGESTIONS):
        self.api_keys = api_keys
        self.cse_id = cse_id
        self.ideal_doc_path = ideal_doc_path
        self.keywords = keywords
        self.num_of_suggestions = num_of_suggestions

    def get_topic(self, query):
        idx = query.find(" OR ")
        if idx == -1:
            return query
        return query[:idx]

    def display_current_keywords(self):
        print(f"\nCurrent Keywords: ", end="")
        for i, keyword in enumerate(self.keywords):
            if i == len(self.keywords) - 1:
                print(keyword)
            else:
                print(f"{keyword}, ", end="")


    def suggest_keywords(self):
        iteration = True
        kg = KeywordGenerator()
        suggested_keywords = set(self.keywords)
        prev_keywords = []

        self.display_current_keywords()

        while iteration:
            # Generate comparison document
            if prev_keywords != self.keywords:
                print("\nGenerating keywords...")
                output_file_path = join(dirname(self.ideal_doc_path), self.get_topic(self.keywords[0]) + ".txt")
                generate_ideal_document(output_file_path, self.api_keys, self.cse_id, depth=1, keywords=self.keywords)
            
            prev_keywords = self.keywords[:] # Deepcopy

            # Extract keywords
            # unigram_keywords, bigram_keywords = kg.generate_keywords_with_keybert(output_file_path)

            '''
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
            '''

            generated_keywords = kg.generate_keywords_with_keybert(output_file_path)
            keyword_suggestions = []
            for keyword in generated_keywords:
                if keyword not in suggested_keywords:
                    keyword_suggestions.append(keyword)
                    suggested_keywords.add(keyword)
                if len(keyword_suggestions) == NUM_SUGGESTIONS:
                    break
            suggested_keywords.update(keyword_suggestions)

            # Let users select keywords to add
            self.display_current_keywords()

            # keyword_suggestions = unigram_suggestions + bigram_suggestions
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
                self.keywords.extend([keyword_suggestions[index] for index in indices])

            while True:
                cont = input(f"Would you like QMOHI to suggest more keywords? (Y/n) : ")
                if cont.lower() in ["y", "yes"]:
                    break
                elif cont.lower() in ["n", "no"]:
                    iteration = False
                    self.display_current_keywords()
                    break

        return self.keywords
