import sys
from os.path import join
from ideal_document_generator import generate_ideal_document
from keyword_generator import KeywordGenerator

OUTPUT_DIR = "./output"

def main():
    kg = KeywordGenerator()

    while True:
        topics = []
        keywords = []
        drugs = []

        print("Press return key to end input and continue to the next step.")

        i = 1
        while True:
            term = input(f"Topics {i} : ")
            if not term:
                break
            topics.append(term)
            i += 1

        i = 1
        while True:
            term = input(f"Keyword {i} : ")
            if not term:
                break
            keywords.append(term)
            i += 1

        i = 1
        while True:
            term = input(f"Drug Name {i} : ")
            if not term:
                break
            drugs.append(term)
            i += 1

        print("\nGenerating ideal document...")
        output_file_path = join(OUTPUT_DIR, topics[0] + ".txt")
        generate_ideal_document(output_file_path, topics, keywords, drugs)

        keyword_suggestion = kg.generate_keywords_with_keybert(output_file_path)
        print(f"\nKeyword Suggestion for {topics[0]}:\n{keyword_suggestion}")

        while True:
            cont = input(f"Continue to next iteration? (Y/n) : ")
            if cont.lower() in ["y", "yes"]:
                break
            elif cont.lower() in ["n", "no"]:
                return


if __name__ == "__main__":
    main()