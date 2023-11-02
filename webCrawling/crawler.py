from databaseIndex import DatabaseIndex
from url_index import Url_Index
from .constraints import *
from .crawler_util import IGNORED_WORDS, get_full_urls

import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO)

# TODO :
#       - move the information extraction to a seperate class (index, or info_extractor) it's not the crawler's job
#       - improve search/traverse method
#       - multi-threading
#       - unify time fomats or handel them
#       - write sequentially to a file / database
#       - handle robots.txt
#       - deal with query parameters in urls
#       - decide what to do with other data types (eg get the text from pdf files, description from images, videos, etc)    
#       --- optemize if needed ---
#
#
#      ------------ maybe ------------
#       - memory issues when scalling up:
#           - write/read intermediate urls to/from a database ( for storage on larger scale)
#           - put limits on in-memory data ( e.g. end process and start new one with one of the unvisited urls)
#           -  
# ---------------------------------------------------------------------------------


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------- Crawler Class --------------------------

class Crawler:
    def __init__(self, *root_urls,
                search_index:DatabaseIndex = None, url_index:Url_Index=None,
                url_constraints:list=None, response_constraints:list=None):
        
        self.root_urls = list(root_urls)

        if search_index:
            self.search_index = search_index
        else:
            self.search_index = DatabaseIndex()
        if url_index:
            self.url_index = url_index
        else:    
            self.url_index = Url_Index()

        try:
            iter(url_constraints)
        except TypeError:
            print("url_constraints should be iterable")
            self.url_constraints = []
        else:
            self.url_constraints = list(url_constraints)
        try:
            iter(response_constraints)
        except TypeError:
            print("response_constraints should be iterable")
            self.response_constraints = [] 
        else:
            self.response_constraints = list(response_constraints)

        self.validate_constraints() # make sure the constraints are valid and fit them to the crawler

    def run(self, search_method:str="dfs", max_iterations:int=1000, requests_timeout:int=8):
        """
        start the crawling process
        args:
            search_method: str, default="bfs", options=["bfs", "dfs"]
            max_iterations: int, default=1000
            requests_timeout: int, default=8(s)
        """
        # if search_method == "bfs" -> pop(0) -> then the urls_to_visit list will be a queue (FIFO)
        # if ( else for now ) search_method == "dfs" -> pop(-1)-> then the urls_to_visit list will be a stack (LIFO)
        very_simple_search_variable = 0 if search_method == "bfs" else -1

        urls_to_visit = list(self.root_urls) 
        visited_urls = set()

        iteration = 0
        while len(urls_to_visit) > 0 and iteration < max_iterations:
            iteration += 1

            logging.info(f" {'#'*10} iteration {iteration} {'#'*10}")

            url = urls_to_visit.pop(very_simple_search_variable) # get the next url to visit
            logging.info(f" URL: {url}")

            if url in visited_urls: # check if the url is visited before
                continue
            logging.debug(" - not visited before")

            if not self.url_requeust_valid(url=url): # check if the url fulfills all constraints, if not, skip it
                continue
            logging.debug(" - valid url")

            # get the response
            response = None
            try:
                response = requests.get(url, timeout=requests_timeout)
            except:
                print(f"Error in getting the response to the url:{url}")
                continue

            if not self.url_process_valid(response): # check if the response fulfills all constraints, if not, skip it
                continue
            logging.debug(" - valid response")

            logging.debug(" - Processing")
            urls, info = self.process_content(url, response) # process the content of the response and extract the urls and info
            logging.debug(" - Done processing")

            for item in urls: # add the extracted urls to the urls_to_visit list
                urls_to_visit.append(item) 

            self.add_to_index(url, info) # add extracted url and info to the search index and url index
            logging.debug(" - Added to index")

            visited_urls.add(url) # update the visited urls set


    def url_requeust_valid(self, url:str):
        """
        check if the url fulfills url constraints
            args:
                url: str
            returns:
                bool
        """
        # execlude the visited recently constraint from the url constraints
        # it will be checked later for wether the info should be processed or not
        # but it has nothing to do with the url validity itself, 
        # we still need to extract the urls from it and continue crawling
        rules_to_apply = [rule for rule in self.url_constraints if isinstance(rule, UrlConstraint) and not isinstance(rule, VisitedRecently)]
        
        for rule in rules_to_apply:
            if not rule(url):
                logging.debug(f" - rule {rule} failed")
                return False
        return True
    
    def url_process_valid(self ,response:requests.models.Response):
        """
        check if the response fulfills response constraints
            args:
                response: requests.models.Response
            returns:
                bool
        """
        for rule in self.response_constraints:
            if not rule(response):
                logging.debug(f" - rule {rule} failed")
                return False
        return True

    def process_content(self, url:str, resopnse:requests.models.Response):
        """
        process the content of the response and extract the urls and info
            args:
                url: str
                resopnse: requests.models.Response
            returns:
                urls: list of urls
                info: dict of words : counts
        """
        # TODO : handle other content types than html / text
        raw_html_content = resopnse.text
        soup = BeautifulSoup(raw_html_content, "html.parser")

        urls = self.get_urls(url, soup)
        info = self.get_info(url, soup)

        return urls, info

    def get_urls(self, url:str, html_content:BeautifulSoup):
        """
        extract the urls from the html content
            args:
                url: str
                html_content: BeautifulSoup
            returns:
                list of urls
        """
        new_urls = [a["href"] for a in html_content.find_all("a") if a.has_attr("href")]
        base_url = html_content.find("base")
        try:
            base_url = base_url["href"]
        except :
            logging.warning(f" No base url found for this page : {url}")
            base_url = url
        
        standarized_urls = get_full_urls(base_url, new_urls)

        return standarized_urls

    def get_info(self,url:str, html_content: BeautifulSoup):  # TODO more enformations
        """
        extract the info from the html content
        get words and their counts
            args:
                url: str
                html_content: BeautifulSoup
            returns:
                dict of words : counts
        """
        global IGNORED_WORDS

        # check if the url is visited recently/not visited recently
        for rule in self.url_constraints:
            if isinstance(rule, VisitedRecently):
                if not rule(url):
                    logging.debug(f" - recently visited, no info processing")
                    return dict()
        
        text = html_content.text
        words = re.findall(r'\b\w+\b', text.lower())
        
        words = [word for word in words if word not in IGNORED_WORDS]
        
        words_counts = Counter(words)
        return words_counts # dict of words : counts

    def add_to_index(self, url, info):
        """
        add the extracted url and info to the search index
        add the url to the unique urls index with the current timestamp of this visit
            args:
                url: str
                info: dict of words : counts
        """
        # add an entries to the search index
        for word, count in info.items():
            self.search_index.add(word, url, count)
        # add the url to the unique urls index with the current timestamp
        self.url_index.add(url, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    def validate_constraints(self):
        """
        check if the constraints are valid and fit them to the crawler
        """
        for constraint in self.url_constraints:
            if isinstance(constraint, VisitedRecently): # TODO do it better
                constraint.set_url_index(self.url_index) # initialize the look_up_index
            if isinstance(constraint, SameDomain):
                constraint.set_domain_urls(self.root_urls) # initialize the root_urls, from whtich the domains will be extracted
            if not isinstance(constraint, UrlConstraint): # check if all url constraint are of type url_constraint
                raise TypeError("url_constraints should be a list of objects of type url_constraints")
        
        for constraint in self.response_constraints:
            if not isinstance(constraint, ResponseConstraint): # check if all response constraint are of type response_constraint
                raise TypeError("response_constraints should be a list of objects of type response_constraints")



