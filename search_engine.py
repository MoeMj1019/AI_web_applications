from flask import Flask, render_template, request, redirect, url_for , abort
from WebSearchEngine.index import WebIndex
from argparse import ArgumentParser


app = Flask(__name__)
app.debug=True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def process():
    # index = WebIndex(args.index_path)
    index = WebIndex("search_index")
    if request.method == 'GET':
        if 'q' in request.args:
            query = request.args['q']
        else:
            query = ""
        links_info = index.search(query)
        return render_template('result.html', query=query, links_info=links_info)

    else:
        return redirect(url_for('index'))
    

import traceback
@app.errorhandler(500)
def internal_error(exception):
   with open("error.log", "a") as f:
         f.write(traceback.format_exc()) 
   return "<pre>"+traceback.format_exc()+"</pre>"

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-p", "--index_path", type=str, default="search_index", help="Index folder")
    parser.add_argument("-d", "--debug", type=bool, default=True ,help="run app in debug mode" ) # debug
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    app.run(host='0.0.0.0')
