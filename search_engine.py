from flask import Flask, render_template, request, redirect, url_for , abort , jsonify
from WebSearchEngine.index import WebIndex
from WebSearchEngine.crawler_util import check_added_content_crawler
from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('seach_engine_flask')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler('logs/flask_search_engine.log', maxBytes=10*1024*1024, backupCount=3)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

logger_crwler = logging.getLogger('to_crawl_queue')
logger_crwler.setLevel(logging.INFO)
handler = RotatingFileHandler('to_crawl_queue.log', maxBytes=10*1024*1024, backupCount=2)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger_crwler.addHandler(handler)

crawler_queue = "crawler_queue.txt"

RESULTS_LIMIT = 20
RESULTS_EXTENTION = 10
SEARCH_INDEX = WebIndex("search_index")
    
app = Flask(__name__)
app.debug=True


@app.route('/search', methods=['POST'])
def add_to_crawler():
    if request.method == 'POST':
        url = request.form['crawlInput']
        logger.info('Crawl input: %s', url)
        processed_input = check_added_content_crawler(url)
        logger.info('Adding %s to crawler', processed_input)
        logger.info('Writing %s to crawler queue', processed_input)
        logger_crwler.info(url)
        return redirect(url_for('start'))
    else:
        logger.warning('Redirecting to stars route')
        return redirect(url_for('start'))

@app.route('/')
def start():
    logger.info('start route accessed')
    return render_template('start.html')

@app.route('/search', methods=['GET'])
def search():
    logger.info('Search route accessed')
    if request.method == 'GET':
        query = request.args.get('q', default='', type=str)
        page = request.args.get('page', default=1, type=int)
        if  page < 1:
            logger.warning('Invalid page number: %s', page)
            page = 1

        logger.info('Query: %s', query)

        links_info , corrected_query, corrected_query_formated = SEARCH_INDEX.search(query, 
                                                                                     page_num=page, 
                                                                                     page_limit=RESULTS_LIMIT if page == 1 else RESULTS_EXTENTION)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # logger.info('AJAX request')
            # logger.info('Query: %s', query)
            # logger.info('Page: %s', page)
            # logger.info('links_info: %s', links_info)
            return jsonify({
                "links_info": links_info,
                "corrected_query": corrected_query,
                "corrected_query_formated": corrected_query_formated
            })
        
        else:
            return render_template('result.html', query=query, links_info=links_info, 
                               corrected_query=corrected_query ,
                               corrected_query_formated=corrected_query_formated)

    else:
        logger.warning('Redirecting to stars route')
        return redirect(url_for('start'))
    

@app.route('/about')
def about():
    logger.info('about route accessed')
    return render_template('about.html')

@app.route('/contact')
def contact():
    logger.info('contact route accessed')
    return render_template('contact.html')

import traceback
@app.errorhandler(500)
def internal_error(error):
   logger.error('Server error: %s', error)
#    with open("internal_error.log", "a") as f:
#          f.write(traceback.format_exc()) 
   return "<pre>"+traceback.format_exc()+"</pre>"

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-p", "--index_path", type=str, default="search_index", help="Index folder")
    parser.add_argument("-d", "--debug", type=bool, default=True ,help="run app in debug mode" ) # debug
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    app.run(host='0.0.0.0')
