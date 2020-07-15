import os
import requests
import operator
import re
import nltk
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from collections import Counter
from bs4 import BeautifulSoup
from stop_words import get_stop_words

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Result


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}

    if request.method == 'POST':
        try:
            url = request.form['url']
            r = requests.get(url)
            print(r.text)
        except:
            errors.append(
                'Unable to get url. Please make sure it is valid url and try again'
            )

            return render_template('index.html', errors=errors)

        if r:
            # text process
            raw = BeautifulSoup(r.text, 'html.parser').get_text()
            nltk.data.path.append('./nltk_data/')
            tokens = nltk.word_tokenize(raw)
            text = nltk.Text(tokens)

            # remove punctuations
            non_punct = re.compile('.*[a-zA-z].*')
            raw_words = [w for w in text if non_punct.match(w)]
            raw_word_count = Counter(raw_words)

            # stop words
            no_stop_words = [w for w in raw_words if w.lower() not in get_stop_words('en')]
            no_stop_words_count = Counter(no_stop_words)

            # save results
            results = sorted(
                no_stop_words_count.items(),
                key=operator.itemgetter(1),
                reverse=True
            )

            try:
                result = Result(
                    url=url,
                    result_all=raw_word_count,
                    result_no_stop_words=no_stop_words_count
                )
                db.session.add(result)
                db.session.commit()
            except:
                errors.append("Unable to add item to the database.")

    return render_template('index.html', errors=errors, results=results)


if __name__ == '__main__':
    app.run()
