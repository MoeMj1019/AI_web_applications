# search engine<WebZone> - AI_and_Web_applications

## Description
this is an implementation of a search engine;
- the seach index is built on top of whoosh library
- the search engine is implemented using flask app

## Installation
see requirements.txt for the required packages
```
pip install -r requirements.txt
```

## Usage
run the flask app
- in debug mode
```
python search_engine.py -i <index_dir>
```
index_dir: the directory of the index to be used by the search engine
- in production mode
```
flask --app search_engine run
```
## Features

### Indexer:
- it's recommended to place all indecies in the <Search_Indecies> directory and the name of their directory should start with "index_" or search_index_" in order to be ignored by git
- the index has a buffer for adding entries, the buffer is commited when it reaches a certain size or when the indexer is closed/deleted
- Schema: 
    url=ID(stored=True, unique=True)  
    title=TEXT(stored=True),  
    description=TEXT(stored=True),  
    time_stamp=DATETIME(stored=True),  
    content=TEXT(analyzer=StemmingAnalyzer(), spelling=True, stored=stored_content)  

### Crawler:
2 crawlers are implemented:
- a sequential crawler
- a parallel crawler <asynchrone>

it has multiple constraints that can be applied in various combinations and in various levels (WebSearchEngine/constraints.py):
- same domain constraint
- valid status code constraint
- valid content type constraint
- valid file extension constraint
- recently visited constraint
- more can be added easily

it be configured to store the content of the crawled pages or store only summary statistics

the async crawler has 2 options to store the content of the crawled pages:
-   write proccesd content to the index directory
-   write raw content temporarly to a directory, process and write later to the index and delete the raw content

the second option has more space for optimazation, sofar the first option is on avarage faster in the whole crawling and storing process  
  

run the sequential or parallel crawler
```
 python run_crawler.py -i <index_dir> -m <max_iteration> -s --async_crawl
```
- -i <index_dir>: preferablly start with Search_Indecies/index_<name> or Search_Indecies/search_index_<name>
- --async_crawl: use the parallel crawler  
- -s: store the content of the crawled pages ( not only summary statistics )   

you can specify the root urls in ROOT_URL in run_crawler.py   
or give a file / stdin of urls to be crawled:
```
<urls> OR file_of_urls | python run_crawler.py -i <index_dir> -m <max_iteration> -s --urls_from_stdin
```
you can configure the constraints in run_crawler.py


### search query:
- the search is implemented sequentially, only a small number of results are searched and returned at a time, more results are generated on demand
- the results of the search are wighted such that they favor AND search and gradully degrade to OR search
- the search query is parsed using a combination of whoosh query parser
- the ranking of the result can be configured with a whoosh scoring object, currently used: BM25F
- query will be SPELLCHECKED, the currected query will be suggested to the user and can be directly used to search

### web interface:
- flask app ( search_engine.py )
- the avaible indecies can be listed and selected for searching as well as adding urls/topics to the crawl queue
- start and search page process the search query display the results
- the inputs are validated and the user is informed of any errors 
- the search query is spellchecked and the corrected query is suggested to the user
- crawl queue page can take input of urls or topics to be considered for crawling in the next iteration ( the crawling based on these inputs is not implemented due to risks involved )
- more search results load dynamically with a load more button
- a simple css design is used, with a some javascript functions, focus is on smooth navigation and ease of use
