import os
from whoosh.index import create_in , open_dir , exists_in , EmptyIndexError
from whoosh.fields import Schema, TEXT, ID , DATETIME
from whoosh.analysis import StemmingAnalyzer
from whoosh.searching import Results
from whoosh.qparser import QueryParser, OperatorsPlugin
from whoosh.spelling import ListCorrector, QueryCorrector, Correction
from whoosh import highlight
from whoosh import spelling
from whoosh import scoring
from whoosh import qparser
from bs4 import BeautifulSoup

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

c_handler = logging.StreamHandler() 
f_handler = RotatingFileHandler('logs/index.log', maxBytes=10*1024*1024, backupCount=2) 
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)

c_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

class WebIndex:
    def __init__(self, index_dir="Search_Indecies/search_index", stored_content=False, name:str=None, max_buffer_size=100, wordlist_path="words_lists/words_list_insane.txt"):
        self.name = name if name and isinstance(name,str) else index_dir
        self.__index_dir = index_dir
        self.schema = Schema(url=ID(stored=True, unique=True),  # THERE HAS TO BE A URL FIELD
                            title=TEXT(stored=True),
                            description=TEXT(stored=True),
                            time_stamp=DATETIME(stored=True),
                            content=TEXT(analyzer=StemmingAnalyzer(), spelling=True, stored=stored_content))
        self.index = self.__initialize_index()
        self.__stored_content = self.index.schema["content"].stored

        self._set_parser()
        self.__correction_cache = dict()
        # self.correctors = {"content": spelling.Corrector()}
        self.wordlist_path = wordlist_path
        self._set_corrector(wordlist_path=wordlist_path)
        self.__add_buffer = []
        self.__max_add_buffer_size = max_buffer_size

    def _set_corrector(self, wordlist_path):
        """
        set the corrector
            args:
                wordlist_path: str
        """
        with open(wordlist_path, "r") as f:
            wordlist = f.read().splitlines()

        self.__word_corrector = ListCorrector(wordlist)  
        correctors = {"content": self.__word_corrector}

        self.__corrector = CostumSimpleQueryCorrector(correctors=correctors)
        self.wordlist_path = wordlist_path

        logger.debug(f"wordlist length: {len(wordlist)}")
        logger.debug(f"wordlist[:10]: {wordlist[:10]}")

        example_query = "cognitiv hume platypose"
        logger.debug(f"self.__word_corrector correction: {self.__word_corrector.suggest(example_query)}")
        logger.debug(f"self.__corrector correction: {self.__corrector.correct_query(q=self.parser.parse(example_query), qstring=example_query)}")




    def _set_parser(self, or_and_scaler=0.9):
        """
        set the parser
            args:
                or_and_scaler: float (between 0 and 1)
        """
        OR_grouping = qparser.OrGroup.factory(or_and_scaler) 
        parser = QueryParser("content", self.index.schema, group=OR_grouping) 
        parser.remove_plugin_class(qparser.FieldsPlugin)
        parser.remove_plugin_class(qparser.WildcardPlugin)
        # parser.add_plugin(qparser.FuzzyTermPlugin())
        parser.replace_plugin(OperatorsPlugin(And="AND", Or="OR", AndMaybe="&", Not="NOT"))

        self.parser = parser

    def add(self, **kwargs): 
        """
        add a new entry to the index
            args:
                **kwargs: dict of the entry attributes
        """
        if not self.entry_has_ID(**kwargs):
            print("Warning: No url<ID> was provided for the entry to be added")
            return 
        kwargs = self.validate_entry(**kwargs)
        # print("kwargs before add_document:", kwargs.keys())
        # print("kwargs before add_document:", [type(kwargs[key]) for key in kwargs.keys()])
        # with self.__get_writer() as writer:
        #         writer.add_document(**kwargs) 
        if len(self.__add_buffer) >= self.__max_add_buffer_size:
            self.commit_add_buffer()
        else:
            self.__add_buffer.append(kwargs)
    
    def commit_add_buffer(self):
        """
        commit the add buffer
        """
        # print(f"commiting {len(self.__add_buffer)} entires from buffer")
        if self.__add_buffer:
            # with self.__get_writer() as writer:
            with self.index.writer() as writer:
                for entry in self.__add_buffer:
                    writer.add_document(**entry) # commiting is done automatically when exiting the context maneger block (writerer closes) 
            self.__add_buffer.clear() # clear the buffer
        

    
    # MAYBE always return a results with full attributes (fill missing attributes with None/"") ?
    # MAYBE no limit by default ?
    def search(self, query_str, page_num=1, page_limit=50, scoring_method:scoring = scoring.BM25F()): 
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
        corrected_str = ""
        corrected_query = ""
        corrected_str_formated = ""
        with self.index.searcher(weighting=scoring_method) as searcher:
            # results = searcher.search(query, limit=limit)
            results = searcher.search_page(query, page_num, pagelen=page_limit)
            processed_results = self.process_search_results(results)

            # simple correction cache check
            if query_str in self.__correction_cache.keys():
                logger.debug(f"CACHED corrected query: {self.__correction_cache[query_str].string}")
                correction = self.__correction_cache[query_str]
            else:
                # correction = searcher.correct_query(query, qstring=query_str)
                correction = self.__corrector.correct_query(q=query, qstring=query_str)
                self.__correction_cache[query_str] = correction
                logger.debug(f"corrected query: {correction.string}")

            correction = self.__corrector.correct_query(q=query, qstring=query_str)
            logger.debug(f"corrected query: {correction.string}")
            # correction = searcher.correct_query(query, qstring=query_str)


            if correction.query != query:
                # print("Did you mean:", corrected.string)
                corrected_str_formated = correction.format_string(hf)
                corrected_str = correction.string
                corrected_query = correction.query

        return processed_results , corrected_str, corrected_str_formated
    
    def process_search_results(self, results:Results):
        """
        process the search results to be returned
            args:
                results: whoosh.searching.Results
            returns:
                tuple of dicts of the results
        """
        # TODO : let the text be highlighted in the frontend
        # TODO : parallelize this / make it faster
        processed_results = []
        for hit in results:
            hit_dict = dict(hit)
            if self.__stored_content:
                highlight = hit.highlights("content")
                hit_dict["highlight"] = highlight
            processed_results.append(hit_dict)
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
    
    def get_all_attributes(self, url, attributes:list):
        """
        get the attributes of the entry with the given url
            args:
                url: str
                attributes: list of str
            returns:
                dict of the attributes
        """
        with self.index.searcher() as searcher:
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
        with self.index.searcher() as searcher:
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
    
    def __del__(self):
        """
        Destructor for the WebIndex class.
        Commits any remaining entries in the __add_buffer upon object destruction.
        """
        try:
            if self.__add_buffer:  # Check if there's anything to commit
                self.commit_add_buffer()
        except Exception as e:
            print(f"Error during WebIndex destruction: {e}")

class CostumSimpleQueryCorrector(QueryCorrector):
    """
    A simple query corrector based on a mapping of field names to
    :class:`Corrector` objects, and a list of ``("fieldname", "text")`` tuples
    to correct. And terms in the query that appear in list of term tuples are
    corrected using the appropriate corrector.
    """

    def __init__(self, correctors, terms=None, aliases=None, prefix=0, maxdist=2):
        """
        :param correctors: a dictionary mapping field names to
            :class:`Corrector` objects.
        :param terms: a sequence of ``("fieldname", "text")`` tuples
            representing terms to be corrected.
        :param aliases: a dictionary mapping field names in the query to
            field names for spelling suggestions.
        :param prefix: suggested replacement words must share this number of
            initial characters with the original word. Increasing this even to
            just ``1`` can dramatically speed up suggestions, and may be
            justifiable since spellling mistakes rarely involve the first
            letter of a word.
        :param maxdist: the maximum number of "edits" (insertions, deletions,
            subsitutions, or transpositions of letters) allowed between the
            original word and any suggestion. Values higher than ``2`` may be
            slow.
        """

        self.correctors = correctors
        self.aliases = aliases or {}
        # ------------------------------------------------------------
        if terms:
            self.termset = frozenset(terms)
        else:
            self.termset = None
        # ------------------------------------------------------------
        self.prefix = prefix
        self.maxdist = maxdist
        logger.debug("SimpleQueryCorrector::__init__ : self.termset = %s", self.termset)

    def correct_query(self, q, qstring):
        correctors = self.correctors
        aliases = self.aliases
        termset = self.termset
        prefix = self.prefix
        maxdist = self.maxdist

        # A list of tokens that were changed by a corrector
        corrected_tokens = []

        # The corrected query tree. We don't need to deepcopy the original
        # because we use Query.replace() to find-and-replace the corrected
        # words and it returns a copy of the query tree.
        corrected_q = q

        # For every word in the original query...
        # Note we can't put these in a set, because we must preserve WHERE
        # in the query each token occured so we can format them later
        # ------------------------------------------------------------
        for token in q.all_tokens():
            fname = token.fieldname
            aname = aliases.get(fname, fname)
            # If this is one of the words we're supposed to correct...
            # if (fname, token.text) in termset:
            if termset and (fname, token.text) not in termset:
                continue
            if isinstance(correctors[fname], ListCorrector):
                if token.text in correctors[fname].wordlist:
                    continue
            c = correctors[aname]
            sugs = c.suggest(token.text, prefix=prefix, maxdist=maxdist)
            if sugs:
                # This is a "simple" corrector, so we just pick the first
                # suggestion :/
                sug = sugs[0]

                # Return a new copy of the original query with this word
                # replaced by the correction
                corrected_q = corrected_q.replace(token.fieldname,
                                                    token.text, sug)
                # Add the token to the list of corrected tokens (for the
                # formatter to use later)
                token.original = token.text
                token.text = sug
                corrected_tokens.append(token)
        # ------------------------------------------------------------

        return Correction(q, qstring, corrected_q, corrected_tokens)
