from os.path import join
from ideal_document_generator import generate_ideal_document
from keyword_generator import KeywordGenerator

OUTPUT_DIR = "./output"
NUM_SUGGESTIONS = 10

def get_topic(query):
    idx = query.find(" OR ")
    if idx == -1:
        return query
    return query[:idx]

def main():
    kg = KeywordGenerator()
    unigram_suggested = set()
    bigram_suggested = set()

    while True:
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

        print("\nGenerating ideal document...")
        output_file_path = join(OUTPUT_DIR, get_topic(keywords[0]) + ".txt")
        generate_ideal_document(output_file_path, keywords)

        unigram_keywords, bigram_keywords = kg.generate_keywords_with_keybert(output_file_path)

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
                return


if __name__ == "__main__":
    main()