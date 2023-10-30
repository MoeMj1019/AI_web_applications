import json

thisDict = { "key": "value"}

with open("safedIndexDataBase.json", 'w') as json_file:
    json.dump(thisDict, json_file)
print("Index DataBase was safed successfully :-)")