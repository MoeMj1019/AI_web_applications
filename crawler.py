from databaseIndex import DatabaseIndex
# import requests

class Crawler:
    def __init__(self, index:DatabaseIndex = None, useRawOutput=False) -> None:
        if index:
            self.index = index
        else:
            self.index = DatabaseIndex()

        self.useRawOutput = useRawOutput


    def start(self,search_method="", max_iterations=1000, *root_urls):
        urls_to_visit = Stack(*root_urls)
        visited_urls = set()

        iterations = 0 
        while not urls_to_visit.isEmpty() and iterations < max_iterations:
            url = urls_to_visit.pop()

            if url in visited_urls:
                continue
            visited_urls.add(url)

            if not self.is_valid_url(url):
                continue

            print("Processing: ", url)
            urls, info = self.process_url(url)

            urls_to_visit.push(urls)
            self.index.add(url, info)
            print("Done processing: ", url)

            iterations += 1

    def is_valid_url(self, url):
        pass

    def process_url(self, url):
        pass

    def get_urls(self, url):
        pass

    def get_info(self, url):
        pass
    



class Stack:
    def __init__(self,  *items) -> None:
        self.container = list(*items)


    def push(self, *item) -> None:
        self.container.append(*item)

    def pop(self) -> object:
        return self.container.pop()
    
    def isEmpty(self):
        return len(self.container) == 0

    def length(self):
        return len(self.container)    
    

class queue:
    def __init__(self,  *items) -> None:
        self.container = list(*items)


    def push(self, *item) -> None:
        self.container.append(*item)

    def pop(self) -> object:
        return self.container.pop(0)
    
    def isEmpty(self):
        return len(self.container) == 0

    def length(self):
        return len(self.container)  

            
            

            




