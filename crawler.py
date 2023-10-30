from databaseIndex import DatabaseIndex
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter


class Crawler:
    def __init__(self, index:DatabaseIndex = None, useRawOutput=False) -> None:
        if index:
            self.index = index
        else:
            self.index = DatabaseIndex()

        self.useRawOutput = useRawOutput

    # 
    def start(self,*root_urls,search_method="bfs", max_iterations=1000, stay_in_domain=True):

        urls_to_visit = list(root_urls)
        
        visited_urls = set()

        iteration = 0 
        while len(urls_to_visit) > 0 and iteration < max_iterations:
            iteration += 1

            url = urls_to_visit.pop()
            print("URL: ", url)
            if url in visited_urls:
                continue

            response = None
            try:
                response = requests.get(url,timeout=8)
            except:
                continue

            if self.is_valid_url(response) and not self.is_visited_recently(url): # TODO check for other statues as well ans sort them out
                
                print("Processing: ", url)
                # print(response.headers)
                # print("###################")
                # print(response.text)
                # print("###################")
                urls, info = self.process_content(url,response.text)

                for item in urls:
                    urls_to_visit.append(item)

                self.add_to_index(url, info)

                # self.index.add(f"key{iteration}", url,15) 
                print("Done processing: ", url)

                visited_urls.add(url)


    def is_valid_url(self, response):
        
        return response.status_code == 200 and "text/html" in response.headers["Content-Type"]

    def add_to_index(self, url, info):
        for word, count in info.items():
            self.index.add(word, url, count)

    def process_content(self, url ,raw_html_content):

        soup = BeautifulSoup(raw_html_content, 'html.parser')

        urls = self.get_urls(url, soup)
        info = self.get_info(soup)

        return urls, info

    def get_urls(self, url, html_content:BeautifulSoup):
        new_urls = [a['href'] for a in html_content.find_all('a') if a.has_attr('href')]

        for i in range(len(new_urls)):
            if new_urls[i].startswith("/"):
                new_urls[i] = url + new_urls[i]
            elif not new_urls[i].startswith("http") or not new_urls[i].startswith("https"):
                url = "/".join(url.split("/")[:-1])
                new_urls[i] = url + "/" + new_urls[i]

        return new_urls

    def get_info(self, html_content:BeautifulSoup): # TODO more enformations
        text = html_content.text
        words = text.split()
        words = [word.lower() for word in words]
        words_counts = Counter(words)
        return words_counts
    
    def is_visited_recently(self, url):
        return False
    

if __name__ == "__main__":
    c = Crawler()
    c.start("https://vm009.rz.uos.de/crawl/index.html", search_method="bfs", max_iterations=1000)

    c.index.safeData()