from WebSearchEngine.crawler import Crawler
from WebSearchEngine.index import WebIndex
from WebSearchEngine.constraints import *
import sys

from argparse import ArgumentParser

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--index_path", type=str, default="search_index", help="Index folder id")
    parser.add_argument("-s", "--store_content", default=False, action="store_true", help="Stored Field for the content in index")
    parser.add_argument("-m", "--max_iterations", type=int, default=1000, help="Maximum number of iterations for the crawler")
    parser.add_argument("--search_method", type=str, default="bfs", help="Search method for the crawler")
    parser.add_argument("--urls_from_stdin", default=False, action="store_true", help="Read the start urls from stdin")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    print("##############################################")
    print("###### index_path : ",args.index_path)
    print("###### store_content : ",args.store_content)
    print("###### max_iterations : ",args.max_iterations)
    print("###### search_method : ",args.search_method)
    print("##############################################")

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

    ROOT_URLS = [
        "https://vm009.rz.uos.de/crawl/index.html",
        "https://www.uni-osnabrueck.de/startseite/",
        "https://en.wikipedia.org/wiki/Cognitive_science",
    ]
    if args.urls_from_stdin:
        ROOT_URLS = []
        for line in sys.stdin:
            ROOT_URLS.append(line.strip())

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