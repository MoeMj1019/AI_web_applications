from .constraints import *
from .index import WebIndex
from .parser import InfoParser
from .crawler_util import get_full_urls

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

# TODO :
#       - write results of each step ( crawling, info extraction, indexing) seperatly to a file/index
#               --> way better seperation of concerns/tasks/checks and better debugging
#       - add default constraints for blausible behaviour without configuration
#       - more advanced traversing/search methods ?? ( sofar only simple bfs and dfs)
#       - multi-threading
#       - handle robots.txt
#       - deal with query parameters in urls
#       - decide what to do with other data types (eg get the text from pdf files, description from images, videos, etc)    
#       --- optemize where needed ---
#
#
#      ------------ maybe ------------
#       - memory issues when scalling up:
#           - put limits on in-memory data
#           -  
# ---------------------------------------------------------------------------------


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------- Crawler Class --------------------------

DEFAULT_CONSTRAINTS = {
    "url_constraints" : (ValidFileExtension(["","html", "htm", "xml","asp","php","jsp","xhtml","shtml","xml","json"])),
    "response_constraints" : (ValidStatusCode(),ValidContentType()),
    "infoExtraction_constraints" : (NotVisitedRecently(time_delta=1, time_unit="days"))
    }

class Crawler:
    """
    Crawler class
    args:
        root_urls: one or more urls to start crawling from (str)
        search_index: WebIndex object, default=None
        info_parser: InfoParser object, default=None
        url_constraints: list of UrlConstraint objects, default=None
        response_constraints: list of ResponseConstraint objects, default=None
        infoExtraction_constraints: list of InfoExtractionConstraint objects, default=None
    """
    def __init__(self, *root_urls,
                search_index:WebIndex = None,
                info_parser:InfoParser = None,
                url_constraints:list=None, 
                response_constraints:list=None, 
                infoExtraction_constraints:list=None,
                search_index_path:str=None):
        
        self.root_urls = list(root_urls)

        if hasattr(search_index, "add") and callable(search_index.add):
            self.search_index = search_index
        elif search_index_path is not None:
            self.search_index = WebIndex(search_index_path)
        else:
            print("No/Not_Valid search index provided, using default")
            self.search_index = WebIndex()

        if hasattr(info_parser, "get_info") and callable(info_parser.get_info):
            self.info_parser = info_parser
        else:
            print("No/Not_Valid info parser provided, using default")
            self.info_parser = InfoParser()

        try:
            iter(url_constraints)
        except TypeError:
            print("url_constraints should be iterable, using default")
            self.url_constraints = DEFAULT_CONSTRAINTS["url_constraints"]
        else:
            self.url_constraints = list(url_constraints)
        try:
            iter(response_constraints)
        except TypeError:
            print("response_constraints should be iterable, using default")
            self.response_constraints = DEFAULT_CONSTRAINTS["response_constraints"]
        else:
            self.response_constraints = list(response_constraints)
        try:
            iter(infoExtraction_constraints)
        except TypeError:
            print("infoExtraction_constraints should be iterable, using default")
            self.infoExtraction_constraints = DEFAULT_CONSTRAINTS["infoExtraction_constraints"]
        else:
            self.infoExtraction_constraints = list(infoExtraction_constraints)

        self.validate_constraints() # make sure the constraints are valid and fit them to the crawler
        
    def run(self, search_method:str="dfs", max_iterations:int=1000, requests_timeout:int=5):
        """
        start the crawling process
        args:
            search_method: str, default="bfs", options=["bfs", "dfs"]
            max_iterations: int, default=1000
            requests_timeout: int, default=5(s)
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

            urls = self.get_urls(url, response) # extract the urls from the response
            for item in urls: # add the extracted urls to the urls_to_visit list
                urls_to_visit.append(item) 
            visited_urls.add(url) # update the visited urls set
            logging.debug(" - extracted urls")

            if not self.url_infoExtraction_valid(url):
                continue
            logging.debug(" - valid for info extraction")

            info = self.info_parser.get_info(url, response) # extract the info from the response
            self.add_to_index(url, info) # add extracted url and info to the search index and url index
            logging.debug(" - Added to index")



    def url_requeust_valid(self, url:str):
        """
        check if the url fulfills url constraints
            args:
                url: str
            returns:
                bool
        """
        for rule in self.url_constraints:
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
    
    def url_infoExtraction_valid(self, url:str):
        """
        check if the url fulfills info extraction constraints
            args:
                url: str
            returns:
                bool
        """
        for rule in self.infoExtraction_constraints:
            if not rule(url):
                logging.debug(f" - rule {rule} failed")
                return False
        return True

    def get_urls(self, url:str, resopnse:requests.models.Response):
        """
        extract the urls from the html content
            args:
                url: str
                resopnse: requests.models.Response
            returns:
                list of urls
        """
        raw_html_content = resopnse.text
        soup_html_content = BeautifulSoup(raw_html_content, "html.parser")
        new_urls = [a["href"] for a in soup_html_content.find_all("a") if a.has_attr("href")]
        base_url = soup_html_content.find("base")
        try:
            base_url = base_url["href"]
        except :
            # logging.warning(f" No base url found for this page : {url}")
            base_url = url
        
        standarized_urls = get_full_urls(base_url, new_urls)

        return standarized_urls

    def add_to_index(self, url, info):
        """
        add the extracted url and info to the search index
            args:
                url: str
                info: dict of info
        """
        self.search_index.add(**info)

    def validate_constraints(self):
        """
        check if the constraints are valid and fit them to the crawler if futher configuration is needed
        """
        for constraint in self.url_constraints:
            if isinstance(constraint, SameDomain):
                constraint.set_domain_urls(self.root_urls) # initialize the root_urls, from whtich the domains will be extracted
            elif not isinstance(constraint, UrlConstraint): 
                raise TypeError("url_constraints should be a list of objects of type url_constraints")
        
        for constraint in self.response_constraints:
            if not isinstance(constraint, ResponseConstraint):
                raise TypeError("response_constraints should be a list of objects of type response_constraints")
            
        for constraint in self.infoExtraction_constraints:
            if isinstance(constraint, VisitedRecently): 
                constraint.set_lookup_index(self.search_index) # initialize the lookup_index
            elif not isinstance(constraint, InfoExtractionConstraint):
                raise TypeError("infoExtraction_constraints should be a list of objects of type infoExtraction_constraints")
            

