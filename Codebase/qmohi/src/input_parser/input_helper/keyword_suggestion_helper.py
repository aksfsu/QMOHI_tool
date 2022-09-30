import re
from os.path import join, dirname
from qmohi.src.input_parser.input_helper.ideal_document_generator import generate_ideal_document
from qmohi.src.input_parser.input_helper.keyword_generator import KeywordGenerator

NUM_UNIGRAM_SUGGESTIONS = 50
NUM_MULTIGRAM_SUGGESTIONS = 50
COMPARISON_DOCUMENT_PATH = "./"


class KeywordSuggestionHelper:
    def __init__(self, api_keys, cse_id, ideal_doc_path, keywords):
        self.api_keys = api_keys
        self.cse_id = cse_id
        self.ideal_doc_path = ideal_doc_path
        self.keywords = keywords

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

    def diversify_keywords_with_hyphen(self, keyword):
        keyword = re.sub(r" +", " ", keyword.lower())
        keyword_variations = [keyword]
        keyword_without_num = re.sub(r"\d+", "", keyword)
        if len(keyword_without_num) > 0 and keyword != keyword_without_num:
            keyword_variations.append(keyword_without_num)
        digit_indices = [(m.start(), m.end()) for m in re.finditer("\d+", keyword)]
        if digit_indices:
            keyword_variation1 = keyword
            keyword_variation2 = keyword
            padding = 0
            for start, end in digit_indices:
                if start != 0 and keyword_variation1[start - 1 + padding] != " ":
                    keyword_variation1 = keyword_variation1[:start + padding] + "-" + keyword_variation1[start + padding:]
                    keyword_variation2 = keyword_variation2[:start + padding] + " " + keyword_variation2[start + padding:]
                    padding += 1
                if end != len(keyword) and keyword_variation1[end + padding] != " ":
                    keyword_variation1 = keyword_variation1[:end + padding] + "-" + keyword_variation1[end + padding:]
                    keyword_variation2 = keyword_variation2[:end + padding] + " " + keyword_variation2[end + padding:]
                    padding += 1
            if padding > 0:
                keyword_variations.append(keyword_variation1)
                keyword_variations.append(keyword_variation2)
        return keyword_variations

    def suggest_keywords(self):
        iteration = 1
        kg = KeywordGenerator()
        suggested_keywords = set(self.keywords)
        prev_keywords = []

        while iteration:
            # Show current keywords
            print(f'\n__Iteration {iteration}__')
            self.display_current_keywords()

            # Initialize drug index offset
            drug_idx = 0
            
            # Generate comparison document
            if prev_keywords != self.keywords:
                prev_keywords = self.keywords[:] # Deepcopy

                print("\nCollecting information...")
                output_file_path = join(dirname(self.ideal_doc_path), self.get_topic(self.keywords[0]) + ".txt")
                if len(self.keywords) <= 3:
                    depth = 2
                else:
                    depth = 1
                extracted_drugs = generate_ideal_document(output_file_path, self.api_keys, self.cse_id, depth=depth, keywords=self.keywords)

                keyword_suggestions = []
                if extracted_drugs:
                    for drug in extracted_drugs:
                        if drug in suggested_keywords:
                            continue
                        drug_variations = self.diversify_keywords_with_hyphen(drug)  
                        keyword_suggestions.extend([drug for drug in drug_variations if drug not in suggested_keywords])
                        suggested_keywords.update(drug_variations)

                # Extract keywords
                print("\nGenerating keywords...")
                extracted_keywords, extracted_keyphrases = kg.generate_keywords_with_keybert(output_file_path)

                # Initialize index offsets
                keyword_idx = 0

                print(f"\nHere Are Suggested Drugs:")
                if keyword_suggestions:
                    for i in range(len(keyword_suggestions)):
                        print(f"{i + 1}: {keyword_suggestions[i]} ")
                    drug_idx = len(keyword_suggestions)
                else:
                    print("No drug to suggest.")

            # Collect new keywords
            for i, keywords in enumerate([extracted_keywords, extracted_keyphrases]):
                for keyword in keywords:
                    if keyword.count(" ") >= 3:
                        continue
                    if keyword in suggested_keywords:
                        continue
                    keyword_variations = self.diversify_keywords_with_hyphen(keyword)  
                    keyword_suggestions.extend(keyword_variations)
                    suggested_keywords.update(keyword_variations)

                    if i == 0 and len(keyword_suggestions) >= drug_idx + keyword_idx + NUM_UNIGRAM_SUGGESTIONS or\
                       i == 1 and len(keyword_suggestions) >= drug_idx + keyword_idx + (NUM_UNIGRAM_SUGGESTIONS + NUM_MULTIGRAM_SUGGESTIONS):
                        break

            # Let users select keywords to add
            print(f"\nHere Are Suggested Keywords:")
            for i in range(drug_idx + keyword_idx, len(keyword_suggestions)):
                print(f"{i + 1}: {keyword_suggestions[i]} ")
            keyword_idx = len(keyword_suggestions)

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
