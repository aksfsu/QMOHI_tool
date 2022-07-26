import sys
import xml.etree.ElementTree as ET

class DrugBankDBHandler:
    def __init__(self):
        self.drugs = []

    def __includes_search_term(self, text, search_term):
        if text:
            if search_term.lower() in text.lower():
                return True
        return False

    def search_drugbank(self, search_term):
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
                            found |= self.__includes_search_term(element.text, search_term)
                            drug["products"].add(element.text)
                            # print(f'product: {element.text}')
                        else:
                            found |= self.__includes_search_term(element.text, search_term)
                            drug["name"] = element.text
                            # print(f'name: {element.text}')
                    elif element.tag == "{http://www.drugbank.ca}group":
                        if self.__includes_search_term(element.text, "approved"):
                            approved = True
                    elif element.tag == "{http://www.drugbank.ca}description":
                        if getDescription:
                            found |= self.__includes_search_term(element.text, search_term)
                            drug["description"] = element.text
                            getDescription = False
                            # print(f'description: {element.text}')
                    elif element.tag == "{http://www.drugbank.ca}indication":
                        if getIndication:
                            found |= self.__includes_search_term(element.text, search_term)
                            drug["indication"] = element.text
                            getIndication = False
                            # print(f'indication: {element.text}')

                    elif element.tag == "{http://www.drugbank.ca}products":
                        getProducts = True
            elif event == "end":
                if element.tag == "{http://www.drugbank.ca}products" or element.tag == "{http://www.drugbank.ca}drug":
                    if found and approved:
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

    def write_to_files(self, output_file_path):
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

'''
# Unit test
import time
def main():
    if len(sys.argv) > 1:
        term = " ".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])
    else:
        print("Search term required")
    
    st = time.time()
    drugbank = DrugBankDBHandler()
    drugbank.search_drugbank(term)
    drugbank.write_to_files("./test.txt")
    et = time.time()
    print(f'Runtime: {et - st}')

if __name__ == "__main__":
	main()
'''