import sys
import xml.etree.ElementTree as ET
from nltk.stem import WordNetLemmatizer

class DrugBankDBHandler:
    def __init__(self, avoid_overlaps=True):
        self.drugs = []
        self.avoid_overlaps = avoid_overlaps
        self.found_drugs = set()

    def __contains_search_term(self, text, search_terms):
        if text and search_terms:
            lemmatizer = WordNetLemmatizer()
            for term in search_terms:
                if " ".join([lemmatizer.lemmatize(word.lower()) for word in term.split()]) in text.lower():
                    return True
        return False

    def search_drugbank(self, descriptive_search_terms=[], specific_search_terms=[]):
        getRecord = False
        for event, element in ET.iterparse("./drugbank_database.xml", events=("start", "end")):
            if event == "start":
                if element.tag == "{http://www.drugbank.ca}drug":
                    drug = {}
                    drug["products"] = set()
                    approved = False
                    getRecord = True
                    getDescription = True
                    getIndication = True
                    getProducts = False
                    found = False
                if getRecord:
                    if element.tag == "{http://www.drugbank.ca}name":
                        if getProducts:
                            found |= self.__contains_search_term(element.text, specific_search_terms)
                            drug["products"].add(element.text)
                            # print(f'product: {element.text}')
                        else:
                            found |= self.__contains_search_term(element.text, specific_search_terms)
                            drug["name"] = element.text
                            # print(f'name: {element.text}')
                    elif element.tag == "{http://www.drugbank.ca}group":
                        if self.__contains_search_term(element.text, ["approved"]):
                            approved = True
                    elif element.tag == "{http://www.drugbank.ca}description":
                        if getDescription:
                            found |= self.__contains_search_term(element.text, descriptive_search_terms)
                            drug["description"] = element.text
                            getDescription = False
                            # print(f'description: {element.text}')
                    elif element.tag == "{http://www.drugbank.ca}indication":
                        if getIndication:
                            found |= self.__contains_search_term(element.text, descriptive_search_terms)
                            drug["indication"] = element.text
                            getIndication = False
                            # print(f'indication: {element.text}')

                    elif element.tag == "{http://www.drugbank.ca}products":
                        getProducts = True
            elif event == "end":
                if element.tag == "{http://www.drugbank.ca}products" or element.tag == "{http://www.drugbank.ca}drug":
                    if found and approved:
                        if self.avoid_overlaps:
                            if not drug["name"] in self.found_drugs:
                                self.found_drugs.add(drug["name"])
                                self.drugs.append(drug)
                        else:
                            self.drugs.append(drug)
                    approved = False
                    getRecord = False
                    getDescription = False
                    getIndication = False
                    getProducts = False
                    found = False
        
        return self.drugs

    def print_results(self):
        print(f"[{len(self.drugs)} records found]")
        for record in self.drugs:
            print("--------------------------\n")
            print(f'Name: {record["name"]}')
            print(f'Description: {record["description"]}')
            print(f'Indication: {record["indication"]}')
            print(f'Products: {record["products"]}')
            print()

    def write_to_file(self, output_file_path):
        print(f"[{len(self.drugs)} records found]")
        with open(output_file_path, "a") as f:
            for drug in self.drugs:
                if drug["name"]:
                    f.write(drug["name"] + "\n")
                if drug["description"]:
                    f.write(drug["description"] + "\n")
                if drug["indication"]:
                    f.write(drug["indication"] + "\n")
                if drug["products"]:
                    f.write(", ".join([p for p in drug["products"] if p]) + "\n")
                f.write("\n")

    def write_to_opened_file(self, f):
        for drug in self.drugs:
            if "name" in drug and drug["name"]:
                f.write(drug["name"] + "\n")
                print(f'{drug["name"]}: ')
            if "description" in drug and drug["description"]:
                f.write(drug["description"] + "\n")
            if "indication" in drug and drug["indication"]:
                f.write(drug["indication"] + "\n")
            if "products" in drug and drug["products"]:
                f.write(", ".join([p for p in drug["products"] if p]) + "\n")
                print(drug["products"])
            f.write("\n")


'''
# Unit test
import time
def main():
    if len(sys.argv) > 1:
        terms = sys.argv[1]
    else:
        print("Search term required")
    
    st = time.time()
    drugbank = DrugBankDBHandler()
    drugbank.search_drugbank(specific_search_terms=terms)
    drugbank.print_results()
    et = time.time()
    print(f'Runtime: {et - st}')

if __name__ == "__main__":
	main()
'''