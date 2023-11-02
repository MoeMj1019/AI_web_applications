from .crawler_util import normalize_time_units
from url_index import Url_Index
from urllib.parse import urljoin , urlparse
from datetime import datetime


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

# ------------------------- response constraint -----------------------------------
class ValidStatusCode(ResponseConstraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        return response.status_code == 200

class ValidContentType(ResponseConstraint):
    def __init__(self) -> None:
        super().__init__()
    def evaluate(self, response):
        return "text/html" in response.headers["Content-Type"]
    
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
                return domain == url_domain or url_domain.endswith("." + domain)
        else:
            return url_domain in self.__domains
        
    def set_domain_urls(self, domain_urls:list):
        self.__domain_urls = domain_urls
        try:
            self.__domains = [urlparse(url).netloc for url in domain_urls]
        except TypeError as e:
            print(e)
            self.__domains = [urlparse(domain_urls).netloc]
    
class VisitedRecently(UrlConstraint):
    def __init__(self,look_up_index:Url_Index=None ,time_delta=60, time_unit="seconds") -> None:
        super().__init__()
        self.time_delta = time_delta
        self.time_unit = time_unit
        self.__time_delta_normalized = normalize_time_units(self.time_delta, self.time_unit)

        self.set_url_index(look_up_index)
        
    def evaluate(self, url:str):
        try:
            last_visit = self.__look_up_index.get(url,"time_stamp")
            last_visit = datetime.strptime(last_visit, "%d/%m/%Y %H:%M:%S")
            time_diff = (datetime.now() - last_visit).total_seconds()
            return time_diff < self.__time_delta_normalized
        
        except (KeyError, TypeError) as e :
            print(e)
            return False
        
    def set_url_index(self, look_up_index:Url_Index):
        if isinstance(look_up_index, Url_Index):
            self.__look_up_index = look_up_index
        else:
            self.__look_up_index = Url_Index() # TODO check if the look_up_index is a valid/usable

    def get_url_index(self):
        return self.__look_up_index
    
class NotVisitedRecently(VisitedRecently):
    def __init__(self,*args,**kwargs) -> None:
        """
        look_up_index:Url_Index=None,
        time_delta=60,
        time_unit="seconds"
        """
        super().__init__(*args,**kwargs)
    
    def evaluate(self,*args,**kwargs):
        """
        url:str
        """
        return not super().evaluate(*args,**kwargs)
    
class ValidFileExtension(UrlConstraint):
    def __init__(self, extensions:list=[]) -> None:
        super().__init__()
        self.extensions = list(extensions)

    def evaluate(self, url):
        parsed_url = urlparse(url)
        suffix = parsed_url.path.split('/')[-1].split('.')[-1] if '.' in parsed_url.path else ""
        return suffix in self.extensions
