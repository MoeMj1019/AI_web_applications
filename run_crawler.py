from webCrawling import *

if __name__ == "__main__":
    # settings
    allowed_extensions = ["","html", "htm", "xml","asp","php","jsp","xhtml","shtml","xml","json"]
    constraints_for_url = [SameDomain(allow_subdomains=True),NotVisitedRecently(time_delta=1, time_unit="days")]
    constraints_for_response = [ValidStatusCode(), ValidContentType()]

    # # initialize the crawler 
    # my_crawler = Crawler(
    #     "https://vm009.rz.uos.de/crawl/index.html",
    #     url_constraints=[SameDomain(allow_subdomains=True),NotVisitedRecently(time_delta=1, time_unit="days")],
    #     response_constraints=[ValidStatusCode(), ValidContentType()],
    # )

    # # start crawling
    # my_crawler.run(
    #     search_method="dfs",
    #     max_iterations=100,
    # )

    # # save the data
    # my_crawler.search_index.saveData()
    # my_crawler.url_index.safe_data()

    # initialize the crawler 
    my_crawler_1 = Crawler(
        "https://vm009.rz.uos.de/crawl/index.html",
        url_constraints=[NotVisitedRecently(time_delta=1, time_unit="days")],
        response_constraints=constraints_for_response,
    )

    # start crawling
    my_crawler_1.run(
        search_method="bfs",
        max_iterations=1,
    )

    # save the data
    my_crawler_1.search_index.saveData()
    my_crawler_1.url_index.safe_data()