import time
import requests
import logging

from db import Session
from models import Article
from article_fetcher import ArticleFetcher
from comment_fetcher import CommentFetcher

TOP_ARTICLES_URL = 'https://hacker-news.firebaseio.com/v0/topstories/.json'
ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'
LIMIT_TOP_RESULTS = 300
REFRESH_INTERVAL = 300


class Refresher:
    def __init__(self, session, article_fetcher, comment_fetcher):
        self.ses = session
        self.article_fetcher = article_fetcher
        self.comment_fetcher = comment_fetcher

    def refresh(self):
        top_article_ids = requests.get(TOP_ARTICLES_URL).json()[:LIMIT_TOP_RESULTS]

        self.article_fetcher.fetch_list(top_article_ids)
        logging.info('Fetched: %s' % (len(top_article_ids)))

        self.update_rank(top_article_ids)
        self.update_scores_and_titles(top_article_ids)

    def update_rank(self, top_article_ids):
        logging.info('Updating ranks...')
        # Updates all to not ranked
        self.ses.query(Article).update({Article.rank: None})

        # If a page is rendered between now and the time the ranks have been updated,
        # it could result in a blank page. Low risk, timing based issue.

        logging.info('New order:')
        for i, article_id in enumerate(top_article_ids):
            arty = self.query_article(article_id)
            if arty:
                arty.rank = i
                logging.info("%s: %s" % (i, article_id))

                submitter = arty.submitter
                # if user on front page isn't tagged yet prioritise them
                submitter.priority = i
            else:
                logging.info('Skipping %s: %s, does not exist' % (i, article_id))

    def collect_comments(self, article_dict):
        logging.info('Collecting child comments...')
        for key in article_dict.keys():
            self.article_fetcher.fetch_list(article_dict[key])

    def update_scores_and_titles(self, top_article_ids):
        logging.info('Updating scores')
        for article_id in top_article_ids:
            article_info = requests.get(ITEM_URL % article_id).json()
            article = self.query_article(article_id)

            if article:
                article.score = article_info.get("score")
                article.number_of_comments = article_info.get("descendants")
                if article_info.get("title") != article.title:
                    logging.debug("Title changed for article %s, from: '%s' to '%s" % (article_id, article_id, article_info.get("title")))
                    article.title = article_info.get("title")
            else:
                logging.debug("Article not found to update, hn_id: %s" % article_id)

    def query_article(self, article_id):
        article = self.ses.query(Article).filter(Article.hn_id == article_id).first()
        return article


def refresh_top():
    # TODO Loop this or reschedule the job?
    print("Starting refresh loop")
    while True:
        start_time = time.time()
        ses = Session()
        arty = ArticleFetcher()
        commy = CommentFetcher()
        refresher = Refresher(ses, arty, commy)
        refresher.refresh()
        ses.commit()

        duration = time.time() - start_time
        logging.info('Loop complete, duration %s' % duration)

        if duration < REFRESH_INTERVAL:
            sleep_time = REFRESH_INTERVAL - duration
            logging.debug("Sleeping for %s seconds" % sleep_time)
            time.sleep(sleep_time)


if __name__ == "__main__":
    refresh_top()
