import logging
import os
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

# Django is only used here to fetch the data from djangodb
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    application = DjangoWhiteNoise(get_wsgi_application())

from dplython import DplyFrame

from article_fetcher import ArticleFetcher
from tagger.models import Article
import pandas as pd


# Trained data
label_df = DplyFrame(pd.read_csv("/Users/danchecketts/PycharmProjects/taggernews/supervised_topics.csv"))

RETRY = True
DEBUG = False
DEBUG_FETCH_MAX = 100
FETCH_NOT_CACHED = True

loops = 0
skipped_due_state = 0
retry_articles = 0
loaded_from_db = 0
uncached_articles = []

for article_id in label_df.id:

    # DEBUG
    if DEBUG and len(uncached_articles) is DEBUG_FETCH_MAX:
        logging.info("Stopped loading articles early due to DEBUG flag")
        break

    try:
        article = Article.objects.get(hn_id=article_id)
        if article.state is None:
            # reparse it again just to get a state assigned
            uncached_articles.append(article_id)
        elif article.state != 0:
            if RETRY:
                retry_articles += 1
                uncached_articles.append(article_id)
            else:
                skipped_due_state += 1
        else:
            loaded_from_db += 1
    except Article.DoesNotExist:
        uncached_articles.append(article_id)

logging.info("Article load stats:")
logging.info("Skipped due to invalid state: " + str(skipped_due_state))
logging.info("Uncached articles: " + str(len(uncached_articles)))
logging.info("Cached articles: " + str(loaded_from_db))

if FETCH_NOT_CACHED:
    logging.info("Fetching articles...")
    articles = ArticleFetcher().fetch(uncached_articles)
    logging.info("Fetched " + str(len(articles)) + " articles. Processing...")
else:
    logging.info("Not attempting to fetch, set FETCH_NOT_CACHED if you want them, this can take a long time.")