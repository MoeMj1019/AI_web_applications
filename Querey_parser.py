class Query_Parser:
    def __init__(self) -> None:
        self.sentence = str
        self.words = list

    def search(self, SearchString):
        self.sentence = SearchString
        self.words = SearchString.split()
        print(self.words)

qP = Query_Parser()
qP.search("Das ist die Suche")