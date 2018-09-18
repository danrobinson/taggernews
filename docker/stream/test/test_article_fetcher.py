import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stream.models import User, Article, Tag, Item
from stream.article_fetcher import ArticleFetcher

from test import dbconn_test, test_user, test_article


class TestArticleFetcher(unittest.TestCase):

    engine = create_engine(dbconn_test)
    Session = sessionmaker(bind=engine)

    def setUp(self):
        self.ses = self.Session()
        self.arty = ArticleFetcher(self.Session())

    def test_smoke(self):
        articles = self.arty.fetch_list([])
        self.assertTrue(articles is not None)
        self.assertFalse(articles)

    def test_load_existing_article(self):
        articles = self.arty.fetch_list([test_article])
        self.assertTrue(articles)
        self.assertTrue(len(articles) == 1)

        db_article = self.ses.query(Article).filter(Article.hn_id == test_article).first()

        self.assertTrue(db_article.hn_id == articles[0].hn_id)

if __name__ == '__main__':
    unittest.main()
