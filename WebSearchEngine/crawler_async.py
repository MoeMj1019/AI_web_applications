import aiohttp
import asyncio
import time
#from bs4 import BeautifulSoup
#from lxml import html
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from .index import WebIndex
from .infoparser import InfoParser
import re
import os
import json
import gzip

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler() 
f_handler = RotatingFileHandler('logs/crawler_async.log', maxBytes=10*1024*1024, backupCount=2) 
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)

c_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

# --------------------------------------------------------------------------------------------------
# curently the write to index is faster, because of lack of time to optimize the write to temporary files and then to index
STORE_TO_INDEX = False # slower but more memory efficient , both in and external memory  
STORE_TO_JSON = False # faster but uses a lot more temporary external memory until the data in indexed and deleted
                        # need time to write files to index
                        # can be Hugely optimized
# --------------------------------------------------------------------------------------------------
INDEX = None
INFO_PARSER = None

def set_store_to_index(store_to_index:bool):
    global STORE_TO_INDEX
    STORE_TO_INDEX = store_to_index

def set_store_to_json(store_to_json:bool):
    global STORE_TO_JSON
    STORE_TO_JSON = store_to_json

def set_index(index:WebIndex):
    global INDEX
    INDEX = index

def set_info_parser(info_parser:InfoParser):
    global INFO_PARSER
    INFO_PARSER = info_parser

def store_to_index(url:str, html:str, index:WebIndex, info_parser:InfoParser):
    info = info_parser.get_info_from_html(url, html)
    index.add(**info)
    logger.debug(f"store_to_index: {url} done")

def set_crawler_content_dir(crawler_content_dir:str):
    global CRAWLER_CONTENT_DIR
    CRAWLER_CONTENT_DIR = crawler_content_dir

# --------------------------------------------------------------------------------------------------
# WARINIG: DO NOT USE THIS CRAWLER FOR LARGE MAX_PAGES VALUES
#          MAKE SURE THE FOMELA BELOW RELUSTS IN LESS THAN 1 MIL PAGES (AROUND )
# should be adjusted to wished max_pages and memory
MAX_CONTENT_PER_FILE = 10
MAX_FILE_PER_FOLDER = 100
MAX_FOLDER_PER_CHUNK = 10
MAX_DATA_CHUNKS = 10 # ensure that there's an (estimated) ubber limit for storage of the crawler data
# max_pages : MAX_CONTENT_PER_FILE * MAX_FILE_PER_FOLDER * MAX_FOLDER_PER_CHUNK * MAX_CHUNKS = 10 * 100 * 10 * 10 = 100,000 pages

CRAWLER_CONTENT_DIR = 'crawler_content'
# --------------------------------------------------------------------------------------------------

class AsyncCrawler:
    def __init__(
            self, 
            start_url, 
            max_pages=100, 
            concurrency=10, 
            file_types:tuple=('', '.html', '.htm', '.xml','.asp','.php','.jsp','.xhtml','.shtml','.xml','.json'),
            file_types_ignore=('ico', 'png', 'jpg', 'jpeg'),
            status_codes=(200,300,301,302,303,304,305,306,307,308)
            ):
        self.start_url = start_url
        self.root_parsed = urlparse(self.start_url)
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.file_types = file_types
        self.file_types_ignore = file_types_ignore
        self.status_codes = status_codes
        self.visited = set()
        self.pages_crawled = 0

        self.timeout = aiohttp.ClientTimeout(total=10)

        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 1)
        self.link_regex = re.compile(r'href="(.*?)"')

        # ----------------------------------------------
        # very simple approach to make use of the AsyncCrawler 
        # store intermediate results (html text) in json files for later procceing (large (temporary) external memory usage)
        # all files will be deleted after the indexing process 
        if STORE_TO_JSON:
            self.html_contents = dict()  # Dictionary to store URL and HTML content
            self.file_counter = 1  # Counter for JSON file naming

            os.makedirs(f"{CRAWLER_CONTENT_DIR}", exist_ok=True)  # Create main data directory
            self.chunk_counter = 1  # Counter for chunk directory
            self.folder_counter = 1  # Counter for folder within chunk
            self.file_counter = 1    # Counter for file within folder
            self.create_directory()
        # ----------------------------------------------

    async def crawl(self):
        print(f'{"-"*40}')
        print(f'async crawl with global variables:')
        print(f'INDEX: {INDEX}')
        print(f'INFO_PARSER: {INFO_PARSER}')
        print(f'STORE_TO_INDEX: {STORE_TO_INDEX}')
        print(f'STORE_TO_JSON: {STORE_TO_JSON}')
        print(f'CRAWLER_CONTENT_DIR: {CRAWLER_CONTENT_DIR}')
        print(f'{"-"*40}')
        print(f'Starting crawl of {self.start_url} with max_pages={self.max_pages} and concurrency={self.concurrency}')

        start_time = time.time()
        self.semaphore = asyncio.Semaphore(self.concurrency)
        queue = deque([self.start_url])  # Use a deque instead of a list
        async with aiohttp.ClientSession() as session:
            tasks = set()
            while queue or tasks:
                # ----------------------------------------------
                if STORE_TO_JSON:
                    if self.chunk_counter > MAX_DATA_CHUNKS:  # Check if maximum chunks limit is reached
                        print("Maximum number of chunks reached. Stopping crawler.")
                        break
                # ----------------------------------------------
                while queue and len(tasks) < self.concurrency and self.pages_crawled < self.max_pages:
                    url = queue.popleft()  # Use popleft instead of pop(0)
                    if url not in self.visited:
                        self.visited.add(url)
                        task = asyncio.ensure_future(self.fetch_and_follow(session, url, queue))
                        tasks.add(task)
                        self.pages_crawled += 1
                if (not queue and not tasks) or self.pages_crawled >= self.max_pages:
                    break
                if tasks:  # Check if tasks is not empty
                    done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = set(tasks)
                self.print_stats(start_time, len(queue))
            if tasks:
                await asyncio.wait(tasks)

        # ----------------------------------------------
        # write remaining html contents to file and clear dictionary
        if STORE_TO_JSON:
            if self.html_contents:
                # self.write_to_json()
                self.write_to_compressed_json()
        
        if STORE_TO_INDEX:
            INDEX.commit_add_buffer() # commit the remaining buffer
        # ----------------------------------------------

    def print_stats(self, start_time, queue_length):
        elapsed_time = time.time() - start_time
        speed = self.pages_crawled / elapsed_time if elapsed_time > 0 else 0
        print(f'\rVisited {self.pages_crawled} pages in {elapsed_time:.2f} seconds ({speed:.2f} pages/second), {queue_length} unvisited links', end='', flush=True)

    async def fetch_and_follow(self, session, url, queue):
        logger.debug(f"fetch_and_follow: {url}")
        async with self.semaphore:
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    logger.debug(f"status_codes: {response.status}")
                    if response.status in self.status_codes:
                        html = await response.text()

                        # store intermediate results (html text) in json files for later procceing
                        # ----------------------------------------------
                        if STORE_TO_JSON:
                            self.store_html_content(url, html)
                        if STORE_TO_INDEX:
                            store_to_index(url, html, INDEX, INFO_PARSER)
                        # ----------------------------------------------

                        loop = asyncio.get_event_loop()
                        try:
                            new_links = await loop.run_in_executor(self.executor, self.extract_links, url, html)
                            logger.debug(f"new links count: {len(new_links)}")
                        except Exception as e:
                            print(f'Exception while extracting links from {url}: {str(e)}')
                            new_links = []
                        queue.extend(new_links)
            except Exception as e:
                #print(f'Exception while fetching {url}: {str(e)}')
                logger.debug(f'Exception while fetching {url}: {str(e)}')
                queue.append(url)  # Re-add the URL to the queue

    #def extract_links(self, base_url, html):
    #    soup = BeautifulSoup(html, 'html.parser')
    #    links = [urljoin(base_url, link.get('href')) for link in soup.find_all('a')]
    #    return [urldefrag(link)[0] for link in links if self.is_valid(link)]

    #def extract_links(self, base_url, html_content):
    #    tree = html.fromstring(html_content)
    #    links = [urljoin(base_url, link) for link in tree.xpath('//a/@href')]
    #    return [urldefrag(link)[0] for link in links if self.is_valid(link)]

    def extract_links(self, base_url, html_content):
        #links = re.findall(r'href="(.*?)"', html_content)
        links = self.link_regex.findall(html_content)
        #absolute_links = set(link if bool(cached_urlparse(link).netloc) else urljoin(base_url, link) for link in links)
        absolute_links = set(urljoin(base_url, link) for link in links)
        return [urldefrag(link)[0] for link in absolute_links if self.is_valid(link)]


    def is_valid(self, url):
        parsed = cached_urlparse(url)
        #root_parsed = urlparse(self.start_url)
        return (parsed.hostname == self.root_parsed.hostname and 
                parsed.scheme in ('http', 'https') and 
                parsed.path.endswith(self.file_types) and
                not parsed.path.endswith(self.file_types_ignore))

# ------------------------------------------------------------------------------------------
    def store_html_content(self, url:str, html:str):
        self.html_contents[url] = html  
        if len(self.html_contents) >= MAX_CONTENT_PER_FILE:
            # self.write_to_json()  # write to file and clear dictionary
            self.write_to_compressed_json()  # write to file and clear dictionary

    # def write_to_json(self):
    #     # path = f"{CRAWLER_CONTENT_DIR}/DATA_CHUNK_{self.chunk_counter}/DATA_FOLDER_{self.folder_counter}/html_contents_{self.file_counter}.json"
    #     filename = f"{self.current_directory}/html_contents_{self.file_counter}.json"
    #     with open(filename, 'w', encoding='utf-8') as file:
    #         json.dump(self.html_contents, file, ensure_ascii=False, indent=4)
    #     self.html_contents.clear()
    #     self.update_counters()

    def write_to_compressed_json(self):
        # Construct the file path
        filename = f'{self.current_directory}/html_contents_{self.file_counter}.json.gz' 
        # Compress and write data
        with gzip.open(filename, 'wt', encoding='utf-8') as file:
            json.dump(self.html_contents, file, ensure_ascii=False)

        self.html_contents.clear()
        self.update_counters()

    def update_counters(self):
        self.file_counter += 1
        if self.file_counter > MAX_FILE_PER_FOLDER:
            self.folder_counter += 1
            self.file_counter = 1
            if self.folder_counter > MAX_FOLDER_PER_CHUNK:
                self.chunk_counter += 1
                self.folder_counter = 1
                if self.chunk_counter > MAX_DATA_CHUNKS:
                    # raise Exception("MAX_DATA_CHUNKS reached")
                    pass
                else:
                    self.create_directory()

            self.create_directory()

    def create_directory(self):
        path = f"{CRAWLER_CONTENT_DIR}/DATA_CHUNK_{self.chunk_counter}/DATA_FOLDER_{self.folder_counter}"
        os.makedirs(path, exist_ok=True)
        self.current_directory = path
# ------------------------------------------------------------------------------------------


@lru_cache(maxsize=None)
def cached_urlparse(url):
    return urlparse(url)

if __name__ == '__main__':

    set_index(WebIndex("SEARCH_INDEX_FROM_ASYNC_CRAWLER", stored_content=True))
    set_info_parser(InfoParser())
    # Usage
    urls = [
                'https://en.wikipedia.org/wiki/Cognitive_science',
                'https://www.uni-osnabrueck.de/startseite/'
                ]
    start_url = urls[1] 

    crawler = AsyncCrawler(start_url, max_pages=1000, concurrency=100)
    #crawler = AsyncCrawler('https://www.uni-osnabrueck.de/startseite/', max_pages=1000, concurrency=100)
    #asyncio.run(crawler.crawl())

    import cProfile
    cProfile.run('asyncio.run(crawler.crawl())', 'results-q.prof')
