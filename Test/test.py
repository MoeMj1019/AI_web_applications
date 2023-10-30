import requests

try:
    response = requests.get("http://info.cern.ch/hypertext/WWW/NeXT/Menus.html")
    print("WORKS")
    print(response)
except:
   print("FAILED")

