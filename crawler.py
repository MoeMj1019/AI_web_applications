from databaseIndex import DatabaseIndex
import requests
from bs4 import BeautifulSoup


class Crawler:
    def __init__(self, index:DatabaseIndex = None, useRawOutput=False) -> None:
        if index:
            self.index = index
        else:
            self.index = DatabaseIndex()

        self.useRawOutput = useRawOutput


    def start(self,*root_urls,search_method="bfs", max_iterations=1000):

        if len(root_urls) > 1:
            urls_to_visit = [*root_urls]
        else:
            urls_to_visit = [root_urls]
        
        visited_urls = set()

        iteration = 0 
        while len(urls_to_visit) > 0 and iteration < max_iterations:
            iteration += 1

            url = urls_to_visit.pop()
            print("URL: ", url)
            if url in visited_urls:
                continue
            visited_urls.add(url)

            if not self.is_valid_url(url):
                continue

            # print("Processing: ", url)
            # urls, info = self.process_url(url)

            # urls_to_visit.push(urls)
            # self.add_to_index(url, info)

            self.index.add(f"key{iteration}", url,15) 
            print("Done processing: ", url)

    def is_valid_url(self, url):
        return True

    def add_to_index(self, url, info):
        pass

    def process_url(self, url):
        urls = self.get_urls(url)
        info = self.get_info(url)

        return urls, info

    def get_urls(self, url):
        pass

    def get_info(self, url):
        pass       

if __name__ == "__main__":
    c = Crawler()
    c.start("wwwsklufgldgflagjfajf.google.com/", "l.csjdkfgdfgksdgfaom", search_method="bfs", max_iterations=10)
    c.index.safeData()