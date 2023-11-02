import json

# # text processing
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('stopwords')
stemmer = PorterStemmer()


class Query_Parser:
    def __init__(self, index_path="safedIndexDataBase.json") -> None:
        self.index_path = index_path
        self.my_dict = dict()
        self.URLWordOccurent = list()
        #load the Index Data Base (Word->Links)
        with open(self.index_path, 'r') as json_file:
            self.my_dict = json.load(json_file)

    def getStemWords(self, SearchString):
        self.sentence = SearchString
        stop_words = set(stopwords.words('english'))
        #extract tokenized stem words from the tet
        words = [stemmer.stem(word) for word in word_tokenize(self.sentence.lower())
            if word.isalpha() and word not in stop_words]
        return words

    def simpleSearch(self, SearchString):
        words = self.getStemWords(SearchString)

        for word in words:
            if word in self.my_dict:
                for entry in self.my_dict[word]:
                    url = entry["URL"]              #extract the url and the freq from a mached result (word found in databese)
                    freq = int(entry["freq"])
                    found = False
                    for element in self.URLWordOccurent:
                        if element[0] == url:
                            element[1] = int(element[1]) + freq 
                            element[2] += 1                     #because we excluded in our database that a key can have the same url value two time, so it musst be the an other key that has the same link (i hope)
                            #print(f"type of element[1] is {type(element[1])} and type of freq is{type(freq)}")
                            found = True
                            #print("entry found (mached)")
                    if found == False:
                        #print(f"new entry appended = {[url, freq, 0]}") 
                        self.URLWordOccurent.append([url, freq, 1]) #the 1 at the end indicates how many different word are found on this link
            else:
                continue

        self.sortFoundedURLs()
        return self.URLWordOccurent
    
    def sortFoundedURLs(self):
        #sort the self.URLWordOccurent
        self.URLWordOccurent.sort(key=lambda x: x[1], reverse=True)
        self.URLWordOccurent = sorted(self.URLWordOccurent, key=lambda x: x[2], reverse=True)
        print(f"###########  {self.URLWordOccurent} ##########")

    