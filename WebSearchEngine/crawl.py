import aiohttp
import asyncio
import time
#from bs4 import BeautifulSoup
#from lxml import html
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import re
import os

class AsyncCrawler:
    def __init__(
            self, 
            start_url, 
            max_pages=100, 
            concurrency=10, 
            file_types=('', '.html', '.htm', '.xml','.asp','.php','.jsp','.xhtml','.shtml','.xml','.json'),
            file_types_ignore=('ico', 'png', 'jpg', 'jpeg'),
            status_codes=(200,)):
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

    async def crawl(self):
        start_time = time.time()
        self.semaphore = asyncio.Semaphore(self.concurrency)
        queue = deque([self.start_url])  # Use a deque instead of a list
        async with aiohttp.ClientSession() as session:
            tasks = set()
            while queue or tasks:
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

    def print_stats(self, start_time, queue_length):
        elapsed_time = time.time() - start_time
        speed = self.pages_crawled / elapsed_time if elapsed_time > 0 else 0
        print(f'\rVisited {self.pages_crawled} pages in {elapsed_time:.2f} seconds ({speed:.2f} pages/second), {queue_length} unvisited links', end='', flush=True)

    async def fetch_and_follow(self, session, url, queue):
        async with self.semaphore:
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status in self.status_codes:
                        html = await response.text()
                        loop = asyncio.get_event_loop()
                        new_links = await loop.run_in_executor(self.executor, self.extract_links, url, html)
                        queue.extend(new_links)
            except Exception as e:
                #print(f'Exception while fetching {url}: {str(e)}')
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

@lru_cache(maxsize=None)
def cached_urlparse(url):
    return urlparse(url)

# Usage
crawler = AsyncCrawler('https://en.wikipedia.org/wiki/Cognitive_science', max_pages=10000, concurrency=400)
#crawler = AsyncCrawler('https://www.uni-osnabrueck.de/startseite/', max_pages=1000, concurrency=100)
#asyncio.run(crawler.crawl())

import cProfile
cProfile.run('asyncio.run(crawler.crawl())', 'results-q.prof')
