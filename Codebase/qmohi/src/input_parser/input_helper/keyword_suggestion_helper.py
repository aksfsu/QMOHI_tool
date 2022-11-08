import re
from os.path import join, dirname
from qmohi.src.input_parser.input_helper.ideal_document_generator import generate_ideal_document
from qmohi.src.input_parser.input_helper.keyword_generator import KeywordGenerator

NUM_UNIGRAM_SUGGESTIONS = 20
NUM_MULTIGRAM_SUGGESTIONS = 20
COMPARISON_DOCUMENT_PATH = "./"


class KeywordSuggestionHelper:
    def __init__(self, api_keys, cse_id, ideal_doc_path, keywords):
        self.api_keys = api_keys
        self.cse_id = cse_id
        self.ideal_doc_path = ideal_doc_path
        self.keywords = keywords
        self.keyword_suggestions = []

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

    def remove_duplicates_from_phrase(self, keyphrase):
        keyphrase_wo_duplicates = []
        for word in keyphrase.split(" "):
            if word not in keyphrase_wo_duplicates:
                keyphrase_wo_duplicates.append(word)
        return " ".join(keyphrase_wo_duplicates)

    def diversify_keywords_with_hyphen(self, keyword):
        keyword_variations = [keyword]

        if re.search(r".*\..*", keyword):
            return keyword_variations

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

    def has_duplicate(self, word):
        if word in self.keywords:
            return True
        for keyword_suggestion in self.keyword_suggestions:
            if word in keyword_suggestion:
                return True
        return False

    def suggest_keywords(self):
        iteration = 1
        kg = KeywordGenerator()
        prev_keywords = []
        offset_idx = 0

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
                depth = 2 if len(self.keywords) <= 3 else 1
                extracted_drugs = generate_ideal_document(output_file_path, self.api_keys, self.cse_id, depth=(2, depth), keywords=self.keywords, drug_details=False)

                if extracted_drugs:
                    for drug in extracted_drugs:
                        if not self.has_duplicate(drug):
                            # Generate different versions of a keyword
                            drug_variations = self.diversify_keywords_with_hyphen(drug)
                            self.keyword_suggestions.append(drug_variations)
                            # Extract first word of a keyphrase
                            if drug_variations[-1].count(" ") > 0:
                                drug_first_word = re.sub(r"\.* .*", "", drug_variations[-1])
                                if len(drug_first_word) >= 3 and not self.has_duplicate(drug_first_word):
                                    self.keyword_suggestions.append([drug_first_word])

                # Extract keywords
                print("\nGenerating keywords...")
                extracted_keywords, extracted_keyphrases = kg.generate_keywords_with_keybert(output_file_path)
                extracted_keyphrases = [self.remove_duplicates_from_phrase(keyphrase) for keyphrase in extracted_keyphrases]

                # Initialize index offsets
                keyword_idx = 0

                print(f"\nHere Are Suggested Drugs:")
                if extracted_drugs:
                    for i in range(offset_idx, len(self.keyword_suggestions)):
                        print(f"{i + 1}: ",end="")
                        for j, keyword in enumerate(self.keyword_suggestions[i]):
                            if j == len(self.keyword_suggestions[i]) - 1:
                                print(keyword)
                            else:
                                print(f"{keyword}, ", end="")
                    drug_idx = len(self.keyword_suggestions)
                else:
                    print("No drug to suggest.")

            # Collect new keywords
            for i, keywords in enumerate([extracted_keywords, extracted_keyphrases]):
                for keyword in keywords:
                    if len(keyword) < 3:
                        continue
                    if keyword.count(" ") >= 3:
                        continue
                    if not self.has_duplicate(keyword):
                        keyword_variations = self.diversify_keywords_with_hyphen(keyword)
                        self.keyword_suggestions.append(keyword_variations)
                    if i == 0 and len(self.keyword_suggestions) >= offset_idx + drug_idx + keyword_idx + NUM_UNIGRAM_SUGGESTIONS or\
                       i == 1 and len(self.keyword_suggestions) >= offset_idx + drug_idx + keyword_idx + (NUM_UNIGRAM_SUGGESTIONS + NUM_MULTIGRAM_SUGGESTIONS):
                        break

            # Let users select keywords to add
            print(f"\nHere Are Suggested Keywords:")
            for i in range(offset_idx + drug_idx + keyword_idx, len(self.keyword_suggestions)):
                print(f"{i + 1}: ",end="")
                for j, keyword in enumerate(self.keyword_suggestions[i]):
                    if j == len(self.keyword_suggestions[i]) - 1:
                        print(keyword)
                    else:
                        print(f"{keyword}, ", end="")

            offset_idx = keyword_idx = len(self.keyword_suggestions)

            print("\nPlease enter the indices of the above suggested keywords you would like to add.")
            print('Please separate each number with ",". You can also combine two or more words with "+".')
            print('For example, given keywords 1: one, 2: two, then you can combine them as a single keyphrase "one two" by inputting "1 + 2".')
            print("You can skip this step by pressing enter.")
            has_error = True
            while has_error:
                has_error = False
                str_indices = input(f"Keyword Indices to Add: ")
                if str_indices:
                    str_indices = [str_index.strip() for str_index in str_indices.split(",") if str_index.strip()]
                    keywords_to_add = []
                    for i, index in enumerate(str_indices):
                        if "+" in index:
                            if "-" in index:
                                has_error = True
                                break
                            parsed_indices = index.split("+")
                            for p_i in range(len(parsed_indices)):
                                parsed_indices[p_i] = parsed_indices[p_i].strip()
                                if not parsed_indices[p_i].isnumeric() or int(parsed_indices[p_i]) <= 0 or int(parsed_indices[p_i]) > len(self.keyword_suggestions):
                                    has_error = True
                                    break
                            parsed_indices = [int(p_i) - 1 for p_i in parsed_indices]
                            for variation_i in range(3):
                                keywords_to_add.append(" ".join([self.keyword_suggestions[index][min(len(self.keyword_suggestions[index]) - 1, variation_i)] for index in parsed_indices]))
                        elif "-" in index:
                            parsed_indices = index.split("-")
                            if len(parsed_indices) > 2:
                                has_error = True
                                break
                            for p_i in range(len(parsed_indices)):
                                parsed_indices[p_i] = parsed_indices[p_i].strip()
                                if not parsed_indices[p_i].isnumeric() or int(parsed_indices[p_i]) <= 0 or int(parsed_indices[p_i]) > len(self.keyword_suggestions):
                                    has_error = True
                                    break
                            parsed_indices = [p_i - 1 for p_i in range(int(parsed_indices[0]), int(parsed_indices[1]) + 1)]
                            for index in parsed_indices:
                                keywords_to_add.extend(self.keyword_suggestions[index])
                        else:
                            if not str_indices[i].isnumeric() or int(str_indices[i]) <= 0 or int(str_indices[i]) > len(self.keyword_suggestions):
                                has_error = True
                                break
                            keywords_to_add.extend(self.keyword_suggestions[int(str_indices[i]) - 1])

                    if has_error:
                        print('"+" and "-" operators cannot be used at the same time.')
                        print('"-" can only be used once for each item.')
                        print('e.g. 1+2-3 or 1-5-10 are invalid.')
                        continue

                    for keyword in keywords_to_add:
                        if keyword not in self.keywords:
                            self.keywords.append(keyword)

            while True:
                cont = input(f"Would you like QMOHI to suggest more keywords? (Y/n) : ")
                if cont.lower() in ["y", "yes"]:
                    iteration += 1
                    break
                elif cont.lower() in ["n", "no"]:
                    iteration = 0
                    self.display_current_keywords()
                    print("\nGenerating the final comparison document...")
                    depth = 2 if len(self.keywords) <= 3 else 1
                    generate_ideal_document(output_file_path, self.api_keys, self.cse_id, depth=(2, depth), keywords=self.keywords, drug_details=True)
                    break

        return self.keywords
