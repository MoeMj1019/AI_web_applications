from flask import Flask, render_template, request, redirect, url_for
from query_Parser import Query_Parser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    parser = Query_Parser()
    if request.method == 'POST':
        word = request.form['word']
        links_info = parser.simpleSearch(word)  # Use your parser to generate the links_info list

        # Pass the data to the 'result.html' template
        return render_template('result.html', processed_word=word, links_info=links_info)

if __name__ == '__main__':
    app.run(debug=True)
