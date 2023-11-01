import os
import json

class Url_Index:
    def __init__(self, file_path="url_index.json"): # data_sets/url_data/url_index.json
        self.file_path = file_path
        if os.path.exists(self.file_path):
            self.my_dict = self.load_data()
        else:
            self.my_dict = dict()
        
    def add(self, url, time_stamp):
        if url not in self.my_dict.keys():
            self.my_dict[url] = {"time_stamp" : time_stamp}
        else:
           self.my_dict[url]["time_stamp"]= time_stamp

    def load_data(self):
        with open(self.file_path, 'r') as json_file:
            loaded_data = json.load(json_file)
        print("Url_Index was loaded successfully :-)")
        return loaded_data
    
    def safe_data(self, file_path=None):
        if file_path is None:
            file_path = self.file_path
        with open(file_path, 'w') as json_file:
            json.dump(self.my_dict, json_file)
        print("Url_Index was saved successfully :-)")

    def get(self, url, attribute="time_stamp"):
        try:
            return self.my_dict[url][attribute]
        except KeyError:
            return None

        
    def __str__(self) -> str:
        return self.my_dict.__str__()
    
    # def __getitem__(self, key):
    #     try:
    #         return self.my_dict[key]
    #     except KeyError:
    #         return None
    