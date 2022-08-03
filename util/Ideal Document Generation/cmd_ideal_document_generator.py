import sys
from os.path import join
from ideal_document_generator import generate_ideal_document
from keyword_generator import KeywordGenerator

OUTPUT_DIR = "./output"

def main():
    while True:
        descriptive_keywords = []
        specific_keywords = []

        while not descriptive_keywords:
            topic = input("Topic (required): ")
            if len(topic) > 0:
                descriptive_keywords.append(topic)

        print("Press return key to end input and continue to the next step.")

        i = 1
        while True:
            term = input(f"Descriptive Keyword {i} : ")
            if not term:
                break
            descriptive_keywords.append(term)
            i += 1

        i = 1
        while True:
            term = input(f"Specific Keyword {i} : ")
            if not term:
                break
            specific_keywords.append(term)
            i += 1

        print("\nGenerating ideal document...")
        output_file_path = join(OUTPUT_DIR, descriptive_keywords[0] + ".txt")
        generate_ideal_document(descriptive_keywords, specific_keywords, output_file_path)
        kg = KeywordGenerator()
        keyword_suggestion = kg.generate_keywords_with_keybert(output_file_path)
        print(f"\nKeyword Suggestion for {descriptive_keywords[0]}:\n{keyword_suggestion}")

        while True:
            cont = input(f"Continue to next iteration? (Y/n) : ")
            if cont.lower() in ["y", "yes"]:
                break
            elif cont.lower() in ["n", "no"]:
                return


if __name__ == "__main__":
    main()