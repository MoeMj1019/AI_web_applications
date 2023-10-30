import pandas as pd

class databaseIndex:
    def __init__(self):
        self.my_dict = {
            "key1" : [{"URL" : "link.com", "freq": 0}, {"URL" : "link2.com", "freq": 20} ]
        }
        print("OK")

    def add(self, key, URL, freq):
        if key not in self.my_dict:
            self.my_dict[key] = [{"URL" : URL, "freq": freq}]
        else:
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
        pass

    def loadData(self):
        pass

dI = databaseIndex()
dI.add("TEST", "test.com", 1)
dI.add("WTF", "WTF.com", 100000)
dI.add("TEST", "linkGehtKlar.com", 100)
print(dI.getData()["TEST"][0])
#dt = pd.DataFrame(dI.getData())
#print(dt)

