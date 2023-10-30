from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        word = request.form['word']
        # You can now process the entered 'word' variable here as needed
        processed_word = word.upper()  # Example: Convert the word to uppercase
        return render_template('result.html', processed_word=processed_word)

if __name__ == '__main__':
    app.run(debug=True)
