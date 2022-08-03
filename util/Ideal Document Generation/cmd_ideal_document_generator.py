import sys
from os.path import join
from ideal_document_generator import generate_ideal_document
from keyword_generator import KeywordGenerator

OUTPUT_DIR = "./output"

def main():
    while True:
        terms = []

        while not terms:
            topic = input("Topic (required): ")
            if len(topic) > 0:
                terms.append(topic)

        i = 1
        while True:
            keyword = input(f"Keyword {i} : ")
            if not keyword:
                break
            terms.append(keyword)
            i += 1
            
        output_file_path = join(OUTPUT_DIR, terms[0] + ".txt")
        generate_ideal_document(terms, output_file_path)
        kg = KeywordGenerator()
        keyword_suggestion = kg.generate_keywords_with_keybert(output_file_path)
        print(f'--- Keyword Suggestion for {terms[0]} ---\n{keyword_suggestion}')

        while True:
            cont = input(f"Continue to next iteration? (Y/n) : ")
            if cont.lower() in ["y", "yes"]:
                break
            elif cont.lower() in ["n", "no"]:
                return


if __name__ == "__main__":
    main()