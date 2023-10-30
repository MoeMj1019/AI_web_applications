import requests
response = requests.get("http://info.cern.ch/hypertext/WWW/TheProject.html")
print(response.text)  # prints the request body (here: HTML content)