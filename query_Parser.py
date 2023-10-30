import json

class Query_Parser:
    def __init__(self) -> None:
        self.sentence = str
        self.words = list
        self.my_dict = dict()
    
        #load the Index Data Base (Word->Links)
        with open("safedIndexDataBase.json", 'r') as json_file:
            my_dict = json.load(json_file)

    def search(self, SearchString):
        self.sentence = SearchString
        self.words = SearchString.split()
        print(self.words)

    