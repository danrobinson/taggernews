# GRRR Enterprises
# 2017-05-13

"""Topic modeling for Hacker News articles."""

from __future__ import print_function

import itertools
import logging
import os
import string
from collections import Counter

import nltk
from django.core.wsgi import get_wsgi_application
from gensim import corpora, models, utils
from nltk.corpus import stopwords
from whitenoise.django import DjangoWhiteNoise

from utils import make_time_filename

# Django is only used here to fetch the data from djangodb
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    application = get_wsgi_application()
    application = DjangoWhiteNoise(application)
# Needs to be imported after django
from tagger.models import Article

nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))
IMPORT_LIMIT = 100
COMMON_WORD_LIMIT = 10000
DICTIONARY_NAME = ".././dictionaries/hn_dictionary"
MODEL_NAME = ".././ml_models/generated/model"
NUM_TOPICS = 100
NUM_PASSES = 10


def all_articletext():
    """Returns all text for articles in the database up to the limit"""
    articles = Article.objects.all().filter(state=0)[:IMPORT_LIMIT]
    logging.info("Selected " + str(len(articles)) + " articles for text tokenisation")
    input_text = []
    for art in articles:
        input_text.append(art.articletext.text)
    return input_text


# Load data
logging.info("Reading articles...")
articletexts = all_articletext()

if not len(articletexts):
    raise RuntimeError("Need articles in the db to run training data on, run fetch_training_data.py first")

# Convert to list of tokens
articletexts = [a.lower() for a in articletexts]
token_list = [list(utils.tokenize(articletext)) for articletext in articletexts]

# Get high frequency words
token_counts = Counter(itertools.chain(*token_list))

# Remove stopwords and punctuation
for word in STOPWORDS:
    del token_counts[word]
for word in string.punctuation:
    del token_counts[word]
del token_counts["|||"]

# Filter for only high frequency tags and stopwords
high_freq = set(token for token, count in token_counts.most_common()[:COMMON_WORD_LIMIT])
token_docs = [[token for token in article_tokens if token in high_freq]
              for article_tokens in token_list]

# Remove empty documents
token_docs = [doc for doc in token_docs if len(doc) > 0]

# Make Gensim dictionary
dictionary = corpora.Dictionary(token_docs)
dict_fname = make_time_filename(DICTIONARY_NAME, ".pkl")
dictionary.save(dict_fname)

# Create corpus for topic model training
corpus = [dictionary.doc2bow(doc) for doc in token_docs]

# Train LDA
model_hi = models.ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=NUM_TOPICS, passes=NUM_PASSES)
model_fname = make_time_filename(MODEL_NAME + "_" + str(NUM_TOPICS) + "topics_" + str(NUM_PASSES) + "pass", ".gensim")
logging.info("Saving model to " + model_fname)
model_hi.save(model_fname)


def label_article(text, trained_model):
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    bow = dictionary.doc2bow(tokens)
    return trained_model[bow]


def show_topics(text, trained_model, n=20):
    topics_and_weights = label_article(text, trained_model)
    for topic, weight in sorted(topics_and_weights, key=lambda x: -x[1]):
        logging.info(weight, topic, trained_model.print_topic(topic, n))
        logging.info()
