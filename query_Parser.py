import json

class Query_Parser:
    def __init__(self) -> None:
        self.sentence = str
        self.words = list
        self.my_dict = dict()
        self.URLWordOccurent = list()
        #load the Index Data Base (Word->Links)
        with open("safedIndexDataBase.json", 'r') as json_file:
            self.my_dict = json.load(json_file)


    def simpleSearch(self, SearchString):
        self.sentence = SearchString
        self.words = SearchString.split()
        print(self.words)
        for word in self.words:
            if word in self.my_dict:
                for entry in self.my_dict[word]:
                    url = entry["URL"]              #extract the url and the freq from a mached result (word found in databese)
                    freq = int(entry["freq"])
                    found = False
                    for element in self.URLWordOccurent:
                        if element[0] == url:
                            element[1] = int(element[1]) + freq 
                            element[2] += 1                     #because we exluded in our database tha a key can have the same url value two time, so it musst be the an other key that has the same link (i hope)
                            #print(f"type of element[1] is {type(element[1])} and type of freq is{type(freq)}")
                            found = True
                            #print("entry found (mached)")
                    if found == False:
                        #print(f"new entry appended = {[url, freq, 0]}") 
                        self.URLWordOccurent.append([url, freq, 1]) #the 1 at the end indicates how many different word are found on this link
            else:
                continue

            print(self.URLWordOccurent)


    