from webCrawling import *

if __name__ == "__main__":
    # settings
    allowed_extensions = ["","html", "htm", "xml","asp","php","jsp","xhtml","shtml","xml","json"]
    constraints_for_url = [SameDomain(allow_subdomains=True),NotVisitedRecently(time_delta=1, time_unit="days")]
    constraints_for_response = [ValidStatusCode(), ValidContentType()]

    # initialize the crawler 
    my_crawler = Crawler(
        "https://vm009.rz.uos.de/crawl/index.html","https://www.uni-osnabrueck.de/startseite/","https://en.wikipedia.org/wiki/Cognitive_science",
        url_constraints=[SameDomain(allow_subdomains=True),NotVisitedRecently(time_delta=1, time_unit="days"),ValidFileExtension(allowed_extensions)],
        response_constraints=[ValidStatusCode(), ValidContentType()],
    )

    # start crawling
    my_crawler.run(
        search_method="bfs",
        max_iterations=1000,
    )

    # save the data
    my_crawler.search_index.saveData()
    my_crawler.url_index.safe_data()