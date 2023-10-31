from databaseIndex import DatabaseIndex
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
from urllib.parse import urljoin , urlparse
import re

# create a Crawler (with url and response constraints)
#     give it one or more urls to start with
#     according to the search method, it will start crawling
#         get a url
#         check if it is valid / wanted to send a request to it
#             send a request and get the response
#         else 
#             go to the next url and repeat
#         check if the response is valid / wanted to process it
#             process the response and get the urls and the info
#             add the current url and the info to the index ( or return them .. etc)
#             add the extracted urls to the list of urls to visit
#         else 
#             go to the next url and repeat

# TODO :
#       - visited recently
#       - write consequently to a file / database
#       - improve search method
#
#       --- optemize

# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------

IGNORED_WORDS = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
            "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
            "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
            "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
            "at", "by", "for", "with", "about", "against", "between", "into", "through", 
            "during", "before", "after", "above", "below", "to", "from", "up", "down", 
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once"
        ])


def get_full_urls(base_url, urls:list):
    standarized_urls = []
    for url in urls:
        absolute_url = urljoin(base_url, url)
        standarized_urls.append(absolute_url)
    return standarized_urls

# ------------------------- constraints ----------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------
class constraint:
    def __init__(self) -> None:
        pass
    def __call__(self, *args, **kwargs):
        return self.evaluate(*args, **kwargs)
    
class url_constraint(constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, url):
        pass

class response_constraint(constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        pass

# ------------------------- response constraint -----------------------------------
class valid_status_code(response_constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        return response.status_code == 200

class valid_content_type(response_constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        return "text/html" in response.headers["Content-Type"]
    
# ------------------------- url constraint -----------------------------------------
class same_domain(url_constraint):
    def __init__(self, root_urls:list="", allow_subdomains=False) -> None:
        super().__init__()
        self.allow_subdomains = allow_subdomains
        try:
            self.domains = [urlparse(url).netloc for url in root_urls]
        except TypeError as e:
            print(e)
            self.domains = [urlparse(root_urls).netloc]

    def evaluate(self, url):
        url_domain = urlparse(url).netloc

        if self.allow_subdomains:
            for domain in self.domains:
                return domain == url_domain or url_domain.endswith("." + domain)
        else:
            return url_domain in self.domains
        
class valid_file_extension(url_constraint):
    def __init__(self, extensions:list=[]) -> None:
        super().__init__()
        self.extensions = list(extensions)

    def evaluate(self, url):
        parsed_url = urlparse(url)
        suffix = parsed_url.path.split('/')[-1].split('.')[-1] if '.' in parsed_url.path else ""
        return suffix in self.extensions



# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------- Crawler Class --------------------------

class Crawler:
    def __init__(self, index: DatabaseIndex = None, useRawOutput=False,
                url_constraints:list=None, response_constraints:list=None,
                stay_in_domain=False):
        
        self.stay_in_domain = stay_in_domain
        self.useRawOutput = useRawOutput

        if index:
            self.index = index
        else:
            self.index = DatabaseIndex()

        try:
            iter(url_constraints)
        except TypeError:
            print("url_constraints is not iterable")
            self.url_constraints = []
        else:
            self.url_constraints = list(url_constraints)

        try:
            iter(response_constraints)
        except TypeError:
            print("response_constraints is not iterable")
            self.response_constraints = [] 
        else:
            self.response_constraints = list(response_constraints)

        # if stay_in_domain:
        #     self.url_constraints.append(is_same_domain())

    def run(self,*root_urls, search_method="bfs", max_iterations=1000, stay_in_domain=True):

        urls_to_visit = list(root_urls)
        visited_urls = set()
        iteration = 0

        if self.stay_in_domain:
            self.url_constraints.append(same_domain(root_urls, allow_subdomains=True))

        while len(urls_to_visit) > 0 and iteration < max_iterations:
            iteration += 1

            url = urls_to_visit.pop()
            print("URL: ", url)
            if url in visited_urls:
                continue

            response = None

            if not self.url_requeust_valid(url=url): # url is visited recently, url refers to data .. etc
                continue

            # get the response
            try:
                response = requests.get(url, timeout=8)
            except:
                print(f"Error in getting the response to the url:{url}")
                continue

            if self.url_process_valid(response):  # TODO check for other statues as well and sort them out
                print("Processing: ", url)
                urls, info = self.process_content(url, response.text)

                for item in urls:
                    urls_to_visit.append(item)

                self.add_to_index(url, info)
                print("Done processing: ", url)

                visited_urls.add(url)


    def url_requeust_valid(self, url):
        for rule in self.url_constraints:
            if not rule(url):
                return False
        return True
    
    def url_process_valid(self ,response): # the rules are functions that should evaluate to true ( the conditions that should be met)
        for rule in self.response_constraints:
            if not rule(response):
                return False
        return True

    def add_to_index(self, url, info):
        for word, count in info.items():
            self.index.add(word, url, count)

    def process_content(self, url, raw_html_content):
        soup = BeautifulSoup(raw_html_content, "html.parser")

        urls = self.get_urls(url, soup)
        info = self.get_info(soup)

        return urls, info

    def get_urls(self, url, html_content: BeautifulSoup):
        new_urls = [a["href"] for a in html_content.find_all("a") if a.has_attr("href")]
        base_url = html_content.find("base")
        try:
            base_url = base_url["href"]
        except :
            print(f"No base url found for this page : {url}")
            base_url = url
        
        standarized_urls = get_full_urls(base_url, new_urls)

        return standarized_urls

    def get_info(self, html_content: BeautifulSoup):  # TODO more enformations
        text = html_content.text
        words = re.findall(r'\b\w+\b', text.lower())
        
        global IGNORED_WORDS
        words = [word for word in words if word not in IGNORED_WORDS]
        
        words_counts = Counter(words)
        return words_counts

    def is_visited_recently(self, url):
        return False


if __name__ == "__main__":
    allowed_extensions = ["","html", "htm", "xml","asp","php","jsp","xhtml","shtml","xml","json"]
    c = Crawler(
        url_constraints=[valid_file_extension(allowed_extensions)],
        response_constraints=[valid_status_code(), valid_content_type()],
        stay_in_domain=True,
    )
    c.run(
        "https://vm009.rz.uos.de/crawl/index.html",
        search_method="bfs",
        max_iterations=1000,
    )

    c.index.safeData()
