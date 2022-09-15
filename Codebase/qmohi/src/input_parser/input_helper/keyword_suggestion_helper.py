import re
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
        iteration = 1
        kg = KeywordGenerator()
        suggested_keywords = set(self.keywords)
        prev_keywords = []

        self.display_current_keywords()

        while iteration:
            # print(f'\n__Iteration {iteration}__')
            # Generate comparison document
            if prev_keywords != self.keywords:
                print("\nGenerating keywords...")
                output_file_path = join(dirname(self.ideal_doc_path), self.get_topic(self.keywords[0]) + ".txt")
                generate_ideal_document(output_file_path, self.api_keys, self.cse_id, depth=1, keywords=self.keywords)
            
                prev_keywords = self.keywords[:] # Deepcopy

                # Extract keywords
                unigram_keywords, bigram_keywords, trigram_keywords = kg.generate_keywords_with_keybert(output_file_path)
            
            # Collect new keywords
            keyword_suggestions = []
            for i, keywords in enumerate([unigram_keywords, bigram_keywords, trigram_keywords]):
                for keyword in keywords:
                    if keyword not in suggested_keywords:
                        digit_indices = [(m.start(), m.end()) for m in re.finditer("\d+", keyword, re.IGNORECASE)]
                        if digit_indices:
                            keyword_variation1 = keyword
                            keyword_variation2 = keyword
                            padding = 0
                            for start, end in digit_indices:
                                if start != 0:
                                    keyword_variation1 = keyword[:start + padding] + "-" + keyword[start + padding:]
                                    keyword_variation2 = keyword[:start + padding] + " " + keyword[start + padding:]
                                    padding += 0
                                if end != len(keyword) and keyword[end + padding] != " ":
                                    keyword_variation1 = keyword[:end + padding] + "-" + keyword[end + padding:]
                                    keyword_variation2 = keyword[:end + padding] + " " + keyword[end + padding:]
                                    padding += 0
                            keyword_suggestions.append(keyword_variation1)
                            keyword_suggestions.append(keyword_variation2) 
                            suggested_keywords.add(keyword_variation1)
                            suggested_keywords.add(keyword_variation2)   
                        keyword_suggestions.append(keyword)
                        suggested_keywords.add(keyword)
                    if i == 0 and len(keyword_suggestions) >= 10 or\
                       i == 1 and len(keyword_suggestions) >= 15 or\
                       i == 2 and len(keyword_suggestions) >= 20:
                        break

            # Let users select keywords to add
            self.display_current_keywords()

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
                    iteration += 1
                    break
                elif cont.lower() in ["n", "no"]:
                    iteration = 0
                    self.display_current_keywords()
                    break

        return self.keywords
