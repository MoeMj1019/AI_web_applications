import json
import os

class DatabaseIndex:
    def __init__(self):
        self.file_path = "safedIndexDataBase.json"
        if os.path.exists(self.file_path):
            self.my_dict = self.loadData()
            print("calling the load function")
        else:        
            self.my_dict = dict()
            print("NOT called the load function")
        print("OK")

    def add(self, key, URL, freq):
        print("adding to the dict")
        if key not in self.my_dict.keys():
            self.my_dict[key] = [{"URL" : URL, "freq": freq}]
        else:
            if key in self.my_dict:
                for URLDict in self.my_dict[key]:
                    if URL == URLDict["URL"]:
                        URLDict["freq"] = freq
                        return
                    
            self.my_dict[key].append({"URL" : URL, "freq": freq})
        #searching for the word in the dict
        #update if accuring
        #   otherwise add it
    
    def getData(self):
        return self.my_dict
    
    #for sorting the entries
    def sort(self):
        pass

    def safeData(self):
        with open(self.file_path, 'w') as json_file:
            json.dump(self.my_dict, json_file)
        print("Index DataBase was safed successfully :-)")    

    def loadData(self):
        with open(self.file_path, 'r') as json_file:
            loaded_data = json.load(json_file)
        print("Index DataBase was loaded successfully :-)")
        return loaded_data

#---Some testing code---
#dI = DatabaseIndex()
#dI.add("TEST", "test.com", 1)
#dI.add("WTF", "WTF.com", 200000)
#dI.add("TEST", "linkGehtKlar.com", 100)
#print(dI.getData())
#dI.safeData()
#-----------------------
