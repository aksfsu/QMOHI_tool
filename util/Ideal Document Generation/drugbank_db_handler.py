import sys
import xml.etree.ElementTree as ET

def includes_search_term(text, search_term):
    if text:
        if search_term.lower() in text.lower():
            return True
    return False

def search_drugbank(search_term):
    drugs = []
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
                        found |= includes_search_term(element.text, search_term)
                        drug["products"].add(element.text)
                        # print(f'product: {element.text}')
                    else:
                        found |= includes_search_term(element.text, search_term)
                        drug["name"] = element.text
                        # print(f'name: {element.text}')
                elif element.tag == "{http://www.drugbank.ca}group":
                    if includes_search_term(element.text, "approved"):
                        approved = True
                elif element.tag == "{http://www.drugbank.ca}description":
                    if getDescription:
                        found |= includes_search_term(element.text, search_term)
                        drug["description"] = element.text
                        getDescription = False
                        # print(f'description: {element.text}')
                elif element.tag == "{http://www.drugbank.ca}indication":
                    if getIndication:
                        found |= includes_search_term(element.text, search_term)
                        drug["indication"] = element.text
                        getIndication = False
                        # print(f'indication: {element.text}')

                elif element.tag == "{http://www.drugbank.ca}products":
                    getProducts = True
        elif event == "end":
            if element.tag == "{http://www.drugbank.ca}products" or element.tag == "{http://www.drugbank.ca}drug":
                if found and approved:
                    drugs.append(drug)
                approved = False
                getRecord = False
                getDescription = False
                getIndication = False
                getProducts = False
                found = False
    
    return drugs

def print_results(drugs):
    print(f"[{len(drugs)} records found]")
    for record in drugs:
        print("--------------------------\n")
        print(f'Name: {record["name"]}')
        print(f'Description: {record["description"]}')
        print(f'Indication: {record["indication"]}')
        print(f'Products: {record["products"]}')
        print()

def write_to_files(fp, drugs):
    print(f"[{len(drugs)} records found]")
    for drug in drugs:
        if drug["name"]:
            fp.write(drug["name"] + "\n")
        if drug["description"]:
            fp.write(drug["description"] + "\n")
        if drug["indication"]:
            fp.write(drug["indication"] + "\n")
        if drug["products"]:
            fp.write(", ".join([p for p in drug["products"] if p]) + "\n")
        fp.write("\n")

def main():
    if len(sys.argv) > 1:
        term = " ".join([str(sys.argv[i]) for i in range(1, len(sys.argv))])
    else:
        print("Search term required")
    
    drugs = search_drugbank(term)
    
    with open("./test.text", "w") as f:
        write_to_files(f, drugs)

if __name__ == "__main__":
	main()
