from WebSearchEngine.crawler import Crawler
from WebSearchEngine.index import WebIndex
from WebSearchEngine.infoparser import InfoParser
from WebSearchEngine.constraints import *
from WebSearchEngine.crawler_async import AsyncCrawler , set_index , set_info_parser , set_store_to_index , set_store_to_json

import sys
import asyncio
import cProfile
from argparse import ArgumentParser

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--index_path", type=str, default="Search_Indecies/search_index", help="Index folder id")
    parser.add_argument("-s", "--store_content", default=False, action="store_true", help="Stored Field for the content in index")
    parser.add_argument("-m", "--max_iterations", type=int, default=1000, help="Maximum number of iterations for the crawler")
    parser.add_argument("--search_method", type=str, default="bfs", help="Search method for the crawler")
    parser.add_argument("--urls_from_stdin", default=False, action="store_true", help="Read the start urls from stdin")
    parser.add_argument("--async_crawl", default=False, action="store_true", help="Use the async crawler")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    print("##############################################")
    print("###### index_path : ",args.index_path)
    print("###### store_content : ",args.store_content)
    print("###### max_iterations : ",args.max_iterations)
    print("###### search_method : ",args.search_method)
    print("###### urls_from_stdin : ",args.urls_from_stdin)
    print("###### async_crawl : ",args.async_crawl)
    print("##############################################")

    ROOT_URLS = [
            "https://vm009.rz.uos.de/crawl/index.html",
            "https://www.uni-osnabrueck.de/startseite/",
            "https://en.wikipedia.org/wiki/Cognitive_science",
        ]
    if args.urls_from_stdin:
            ROOT_URLS = []
            for line in sys.stdin:
                ROOT_URLS.append(line.strip())
    
    # configuration for the crawler
    INDEX = WebIndex(f"{args.index_path}",
                     stored_content=args.store_content)
    
    allowed_extensions = ["","html", "htm", "xml","asp","jsp","xhtml","shtml","xml","json"]
    constraints_for_url = [
                                SameDomain(allow_subdomains=True),
                                ValidFileExtension(allowed_extensions)
                            ]
    constraints_for_response = [
                                    ValidStatusCode(),
                                    ValidContentType()
                                ]
    constraints_for_infoExtraction = [
                                        NotVisitedRecently(time_delta=1, time_unit="days")
                                        ]
    if args.async_crawl:
        start_url = ROOT_URLS[0]
        set_store_to_index(True)
        set_index(INDEX)
        set_info_parser(InfoParser())
        crawler = AsyncCrawler(start_url, max_pages=args.max_iterations, concurrency=200,
                               file_types=allowed_extensions)
        asyncio.run(crawler.crawl())
        # cProfile.run('asyncio.run(crawler.crawl())', 'results-q.prof')

    else:
        # initialize the crawler 
        my_crawler = Crawler(
            *ROOT_URLS,
            search_index=INDEX,
            url_constraints = constraints_for_url,
            response_constraints = constraints_for_response,
            infoExtraction_constraints = constraints_for_infoExtraction,
        )

        # start crawling
        my_crawler.run(
            search_method=args.search_method,
            max_iterations=args.max_iterations,
            requests_timeout=5,
        )