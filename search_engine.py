from flask import Flask, render_template, request, redirect, url_for , abort , jsonify
from WebSearchEngine.index import WebIndex
from WebSearchEngine.crawler_util import check_added_content_crawler
from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler
import os
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
SEARCH_INDEX = WebIndex("Search_Indecies/search_index", name="Main Index")
INDEX_NAME = SEARCH_INDEX.name
AVAILABLE_INDEXES = {
                    'Main Index': 'Search_Indecies/search_index',   
                    'Demo Index': 'Search_Indecies/search_index_demo',
                    }
    
app = Flask(__name__)
app.debug=True


def set_main_index(index_name):
    global SEARCH_INDEX, INDEX_NAME, AVAILABLE_INDEXES
    if index_name not in AVAILABLE_INDEXES:
        logger.warning('Index name %s not found in available indecies', index_name)
        return
    if index_name == INDEX_NAME:
        logger.info('Index name %s is already set', index_name)
        return
    if not os.path.exists(AVAILABLE_INDEXES[index_name]):
        logger.info(f'Index dos not exist, creating new index {index_name} | {AVAILABLE_INDEXES[index_name]}')
    logger.info(f'Index set to {index_name} | {AVAILABLE_INDEXES[index_name]}')
    SEARCH_INDEX = WebIndex(AVAILABLE_INDEXES[index_name] , name=index_name)
    INDEX_NAME = SEARCH_INDEX.name


@app.route('/')
def start():
    logger.info('start route accessed')
    return render_template('start.html', index_name=INDEX_NAME, available_indecies=AVAILABLE_INDEXES.keys())

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
                               corrected_query_formated=corrected_query_formated,
                               index_name=INDEX_NAME,
                               available_indecies=AVAILABLE_INDEXES.keys())

    else:
        logger.warning('Redirecting to stars route')
        return redirect(url_for('start'))
    
@app.route('/', methods=['POST'])
def add_to_crawler():
    if request.method == 'POST':
        url = request.form['crawlInput']
        logger.info(f'Crawl input: {url}')
        processed_input = check_added_content_crawler(url)
        logger.info(f'Writing {INDEX_NAME}, {processed_input} to crawler queue')
        logger_crwler.info(f'{INDEX_NAME}, {processed_input}')
        return redirect(url_for('crawl_queue'))
    else:
        logger.warning('Redirecting to start route')
        return redirect(url_for('start'))
    
@app.route('/personalize_search_space')
def crawl_queue():
    return render_template('crawl_queue.html', index_name=INDEX_NAME, available_indecies=AVAILABLE_INDEXES.keys())
    
@app.route('/set_index', methods=['POST'])
def set_index():
    logger.info('set_index route accessed')
    try:
        chosen_index = request.form['index']
        # Update the main index here, e.g., session['main_index'] = chosen_index
        set_main_index(chosen_index)
        return jsonify({'status': 'success', 'index': chosen_index})
    except Exception as e:
        # Log the exception for debugging
        print("Error in set_index:", e)
        logger.error('Error in set_index: %s', e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

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
   with open("internal_error.log", "a") as f:
         f.write(traceback.format_exc()) 
   return "<pre>"+traceback.format_exc()+"</pre>"

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--index_path", type=str, default="Search_Indecies/search_index", help="Index folder")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Port to run the server on")
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    app.run(port=args.port, host='0.0.0.0')
