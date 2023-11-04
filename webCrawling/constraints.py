from .crawler_util import normalize_time_units
from .index import WebIndex 
from urllib.parse import urlparse
from datetime import datetime

# ------------------------- constraints base classes -------------------------
class Constraint:
    def __init__(self) -> None:
        pass
    def __call__(self, *args, **kwargs):
        return self.evaluate(*args, **kwargs)
    def __str__(self) -> str:
        return f"constraint: {type(self).__name__}"
    
class UrlConstraint(Constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, url):
        pass

class ResponseConstraint(Constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        pass

class InfoExtractionConstraint(Constraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, url):
        pass

# ------------------------- response constraint -----------------------------------
class ValidStatusCode(ResponseConstraint): 
    def __init__(self, valid_codes:list=[200]) -> None:
        super().__init__()
        self.valid_codes = valid_codes
    def evaluate(self, response):
        try:
            return response.status_code in self.valid_codes
        except TypeError as e:
            print(e)
            return False

class ValidContentType(ResponseConstraint): 
    def __init__(self, valid_content:list=["text/html"]) -> None:
        super().__init__()
        self.valid_content = valid_content
    def evaluate(self, response):
        try:
            return any([content_type in response.headers["Content-Type"] for content_type in self.valid_content])
        except TypeError as e:
            print(e)
            return False
    
# ------------------------- url constraint -----------------------------------------
class SameDomain(UrlConstraint): # TODO handle redirects 
    def __init__(self, domain_urls:list="", allow_subdomains=False) -> None:
        super().__init__()
        self.allow_subdomains = allow_subdomains
        self.set_domain_urls(domain_urls)

    def evaluate(self, url):
        url_domain = urlparse(url).netloc
        if self.allow_subdomains:
            for domain in self.__domains:
                if domain == url_domain or url_domain.endswith("." + domain):
                    return True
            return False
            # return any([domain == url_domain or url_domain.endswith("." + domain) for domain in self.__domains ]) 
        else:
            for domain in self.__domains:
                if domain == url_domain:
                    return True
            return False
            # return any([domain == url_domain for domain in self.__domains ])          
        
    def set_domain_urls(self, domain_urls:list):
        self.__domain_urls = domain_urls
        try:
            self.__domains = [urlparse(url).netloc for url in domain_urls]
        except TypeError as e:
            print(e)
            self.__domains = [urlparse(domain_urls).netloc]
            
class ValidFileExtension(UrlConstraint):
    def __init__(self, extensions:list=[]) -> None:
        super().__init__()
        self.extensions = list(extensions)

    def evaluate(self, url):
        parsed_url = urlparse(url)
        suffix = parsed_url.path.split('/')[-1].split('.')[-1] if '.' in parsed_url.path else ""
        return suffix in self.extensions

# ------------------------- info extraction constraint -----------------------------
class VisitedRecently(InfoExtractionConstraint):
    def __init__(self,look_up_index:WebIndex=None ,time_delta=60, time_unit="seconds") -> None:
        super().__init__()
        self.time_delta = time_delta
        self.time_unit = time_unit
        self.__time_delta_normalized = normalize_time_units(self.time_delta, self.time_unit)

        # TODO better logic
        # it's easier when the crawler writes to intermediate files --> no need to pass the index from the crawler
        if isinstance(look_up_index,WebIndex):  
            self.__lookup_index = look_up_index
        else:
            self.__lookup_index = None     
            print("VisitedRecently::__init__() : VisitedRecently object with no/not valid lookup_index is created,configure a the lookup_index using set_lookup_index method")   
            print("     - the obove warning will keep everytime the constraint is evaluated/used until a valid lookup_index is set")
    def evaluate(self, url:str):
        if self.__lookup_index is None:
            print("VisitedRecently::evaluate : VisitedRecently object with no/not valid lookup_index is created,configure a the lookup_index using set_lookup_index method")
            return False
        
        last_visit = self.__lookup_index.get_attribute(url,"time_stamp")
        if last_visit is None:
            return False
        if not isinstance(last_visit, datetime):
            print("last_visit is not a datetime object !?")
            return False
        
        time_diff = (datetime.now() - last_visit).total_seconds()
        return time_diff < self.__time_delta_normalized
        
    def set_lookup_index(self, look_up_index:WebIndex):
        if self.__lookup_index is not None:
            return
        if isinstance(look_up_index, WebIndex):
            self.__lookup_index = look_up_index
        else:
            self.__lookup_index = WebIndex() 

    def get_lookup_index(self):
        return self.__lookup_index
    
class NotVisitedRecently(VisitedRecently):
    def __init__(self,*args,**kwargs) -> None:
        """
        look_up_index:WebIndex=None,
        time_delta=60,
        time_unit="seconds"
        """
        super().__init__(*args,**kwargs)
    
    def evaluate(self,*args,**kwargs):
        """
        url:str
        """
        return not super().evaluate(*args,**kwargs)
