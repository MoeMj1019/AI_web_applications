import os
from whoosh.index import create_in , open_dir , exists_in , EmptyIndexError
from whoosh.fields import Schema, TEXT, ID , DATETIME
from whoosh.analysis import StemmingAnalyzer
from whoosh.searching import Results
from whoosh.qparser import QueryParser, OperatorsPlugin
from whoosh import highlight
from whoosh import spelling
from whoosh import qparser
from bs4 import BeautifulSoup

class WebIndex:
    def __init__(self, index_dir="search_index", stored_content=False):
        self.__index_dir = index_dir
        self.schema = Schema(url=ID(stored=True, unique=True),  # THERE HAS TO BE A URL FIELD
                            title=TEXT(stored=True),
                            description=TEXT(stored=True),
                            time_stamp=DATETIME(stored=True),
                            content=TEXT(analyzer=StemmingAnalyzer(), spelling=True, stored=stored_content))
        self.index = self.__initialize_index()
        self.__stored_content = self.index.schema["content"].stored

        self.set_parser()
        # self.correctors = {"content": spelling.Corrector()} 

    def set_parser(self, or_and_scaler=0.9):
        """
        set the parser
            args:
                or_and_scaler: float (between 0 and 1)
        """
        OR_grouping = qparser.OrGroup.factory(or_and_scaler) 
        parser = QueryParser("content", self.index.schema, group=OR_grouping) 
        parser.remove_plugin_class(qparser.FieldsPlugin)
        parser.remove_plugin_class(qparser.WildcardPlugin)
        parser.add_plugin(qparser.FuzzyTermPlugin())
        parser.replace_plugin(OperatorsPlugin(And="AND", Or="OR", AndMaybe="&", Not="NOT"))

        self.parser = parser

    def add(self, **kwargs): 
        """
        add a new entry to the index
            args:
                **kwargs: dict of the entry attributes
        """
        if not self.entry_has_ID(**kwargs):
            print("Warning: No url was provided for the entry to be added")
            return 
        kwargs = self.validate_entry(**kwargs)
        # print("kwargs before add_document:", kwargs.keys())
        # print("kwargs before add_document:", [type(kwargs[key]) for key in kwargs.keys()])
        with self.__get_writer() as writer:
            writer.add_document(**kwargs) # commiting is done automatically when exiting the with block (writerer closes) 
    
    # MAYBE always return a results with full attributes (fill missing attributes with None/"") ?
    # MAYBE no limit by default ?
    def search(self, query_str, limit=None): 
        """
        search the index for the query
            args:
                query_str: str
                limit: int
            returns:
                tuple of dicts of the results
        """                     
        query = self.parser.parse(query_str)   
        hf = highlight.HtmlFormatter()            
        processed_results = None
        corrected_str = None
        corrected_query = None
        corrected_str_formated = None
        # with self.__get_searcher() as searcher:
        with self.index.searcher() as searcher:
            # query = QueryParser("content", self.index.schema).parse(query_str)
            # corrected = searcher.correct_query(query, qstring=query_str)
            correction = searcher.correct_query(query, qstring=query_str)

            if correction.query != query:
                # print("Did you mean:", corrected.string)
                corrected_str_formated = correction.format_string(hf)
                corrected_str = correction.string
                corrected_query = correction.query
            results = searcher.search(query, limit=limit)
            processed_results = self.process_search_results(results)

        return processed_results , corrected_str, corrected_str_formated
    
    def process_search_results(self, results:Results):
        """
        process the search results to be returned
            args:
                results: whoosh.searching.Results
            returns:
                tuple of dicts of the results
        """
        processed_results = [dict(hit) for hit in results]
        if self.__stored_content:
            highlights = [hit.highlights("content") for hit in results] # TODO : parallelize this / make it faster
            # strip html tags used for highlighting TODO : let the text be highlighted in the frontend
            # highlights = [BeautifulSoup(highlight, "html.parser").get_text() for highlight in highlights]
            for i, highlight in enumerate(highlights):
                processed_results[i]["highlight"] = highlight
        return tuple(processed_results)
    
    def entry_has_ID(self, **kwargs):
        """
        check if the entry has an ID
            args:
                **kwargs: dict of the entry attributes
            returns:
                bool
        """
        return "url" in kwargs.keys()
    
    def validate_entry(self, **kwargs):
        """
        validate the entry attributes to be added to the index (remove invalid attributes)
            args:
                **kwargs: dict of the entry attributes
            returns:    
                dict of the valid attributes
        """
        valid_keys = set(self.index.schema.names())
        return {key: value for key, value in kwargs.items() if key in valid_keys}
    
    def get_attributes(self, url, attributes:list):
        """
        get the attributes of the entry with the given url
            args:
                url: str
                attributes: list of str
            returns:
                dict of the attributes
        """
        with self.__get_searcher() as searcher:
            try:
                attributes_dict = dict()
                docnum = searcher.document_number(url=url)
                for attribute in attributes:
                    if attribute in searcher.stored_fields(docnum).keys():
                        attributes_dict[attribute] = searcher.stored_fields(docnum)[attribute]
                return attributes_dict
                # return {attribute : searcher.stored_fields(docnum)[attribute] for attribute in attributes 
                #                 if attribute in searcher.stored_fields(docnum).keys()}
            except Exception as e:
                # print(e)
                return None
            
    def get_attribute(self, url, attribute):
        """
        get the attribute of the entry with the given url
            args:
                url: str
                attribute: str
            returns:
                attribute value
        """
        with self.__get_searcher() as searcher:
            try:
                docnum = searcher.document_number(url=url)
                if attribute in searcher.stored_fields(docnum).keys():
                    return searcher.stored_fields(docnum)[attribute]
            except Exception as e:
                # print(e)
                return None
    
    def get_stored_content(self):
        """
        get the __stored_content attribute
            returns:
                bool
        """
        return self.__stored_content
    
    def __initialize_index(self):
        """
        initialize the index
            returns:
                whoosh.index.Index
        """
        if not os.path.exists(self.__index_dir):
            os.makedirs(self.__index_dir)
        try:
            return open_dir(self.__index_dir)
        except EmptyIndexError:
            return create_in(self.__index_dir, self.schema)
        except Exception as e:
            if not exists_in(self.__index_dir):
                return create_in(self.__index_dir, self.schema)
            raise e
        
    def __get_writer(self):
        return self.index.writer()
    
    def __get_searcher(self):
        return self.index.searcher()
    
    def __str__(self) -> str:
        return self.index.__str__()
    