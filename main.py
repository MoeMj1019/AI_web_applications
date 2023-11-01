from flask import Flask, render_template, request, redirect, url_for
from query_Parser import Query_Parser
from argparse import ArgumentParser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    parser = Query_Parser(args.index_path)
    if request.method == 'POST':
        word = request.form['word']
        links_info = parser.simpleSearch(word)  # Useing the parser to generate the links_info list

        # Pass the data to the 'result.html' template
        return render_template('result.html', processed_word=word, links_info=links_info)


def get_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--index_path", type=str, default="safedIndexDataBase.json", help="Index folder")
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    app.run(debug=True)
