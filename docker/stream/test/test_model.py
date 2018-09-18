import time
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from docker.stream.stream.models import User, Article, Tag, Item
from . import dbconn_test, test_user, test_article


class TestModel(unittest.TestCase):
    engine = create_engine(dbconn_test)
    Session = sessionmaker(bind=engine)

    def setUp(self):
        self.ses = self.Session()

    def user(self):
        return self.ses.query(User).filter(User.id == test_user).first()

    def test_tags_loaded(self):
        tags = self.ses.query(Tag).all()

        self.assertTrue(len(tags) > 0)
        print(("Loaded %s tags" % str(len(tags))))

    def test_tags_rel_url(self):
        tag = self.ses.query(Tag).first()

        self.assertTrue(tag.name.lower() in tag.get_relative_url())

    def test_user(self):
        user = self.user()
        self.assertTrue(user)

    def test_article(self):
        article = self.ses.query(Article).filter(Article.hn_id == test_article).first()
        self.assertTrue(article)

    def test_article_user_mapping(self):
        article = self.ses.query(Article).filter(Article.hn_id == test_article).first()
        self.assertTrue(article)

        self.assertTrue(article.submitter)

    def test_article_text_mapping(self):
        article = self.ses.query(Article).filter(Article.hn_id == test_article).first()
        self.assertTrue(article)

        self.assertTrue(article.text)
        print("Length of text: " + str(len(article.text.text)))

    def test_article_tag_mapping(self):
        article = self.ses.query(Article).filter(Article.hn_id == test_article).first()
        self.assertTrue(article)

        self.assertTrue(len(article.tags) > 0)

    def test_user_item_mapping(self):
        user = self.ses.query(User).filter(User.id == test_user).first()

        self.assertTrue(len(user.items) > 0)
        print(user.items[0].submitter)
        self.assertTrue(user.items[0].submitter == user)

    def test_user_article_mapping(self):
        user = self.ses.query(User).filter(User.id == test_user).first()

        self.assertTrue(len(user.articles) > 0)
        self.assertTrue(user.articles[0].submitter == user)

    def test_item_parent_mapping(self):
        item = self.ses.query(Item).filter(Item.parent != None).first()

        self.assertTrue(item.parent)
        self.assertTrue(isinstance(item.parent, Item))

    def test_item_top_parent_mapping(self):
        item = self.ses.query(Item).filter(Item.top_parent != None).first()

        self.assertTrue(item.top_parent)
        self.assertTrue(isinstance(item.top_parent, Article))

    def test_user_all_articles_is_superset(self):
        user = self.user()
        self.assertTrue(user)

        all_articles = user.all_articles()
        articles = user.articles

        self.assertFalse(all_articles == articles, "Articles and all_articles are equal")
        self.assertTrue(set.issubset(all_articles, articles), "Articles is not a subset")

    def test_user_all_articles_contains_other_submitters(self):
        user = self.user()

        all_articles = user.all_articles()
        submitter_different = False
        for article in all_articles:
            if article.submitter != user:
                submitter_different = True

        self.assertTrue(submitter_different, "None of the articles in the superset were submitted by another user")

    def test_user_tag_compilation(self):
        user = self.user()
        tags = user.get_tags()

        self.assertTrue(len(tags) > 0)

    def test_article_age(self):

        article = Article()
        article.timestamp = datetime.utcnow().timestamp()

        article.timestamp = (datetime.utcnow() - timedelta(seconds=1)).timestamp()
        age_output = article.age()
        self.assertEqual("0 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(seconds=29)).timestamp()
        age_output = article.age()
        self.assertEqual("0 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(seconds=30)).timestamp()
        age_output = article.age()
        self.assertEqual("1 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(minutes=2)).timestamp()
        age_output = article.age()
        self.assertEqual("2 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(minutes=2, seconds=7)).timestamp()
        age_output = article.age()
        self.assertEqual("2 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(minutes=2, seconds=30)).timestamp()
        age_output = article.age()
        self.assertEqual("3 minutes", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(hours=2)).timestamp()
        age_output = article.age()
        self.assertEqual("2 hours", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(hours=2, minutes=29, seconds=59)).timestamp()
        age_output = article.age()
        self.assertEqual("2 hours", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(hours=2, minutes=30)).timestamp()
        age_output = article.age()
        self.assertEqual("3 hours", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(days=2)).timestamp()
        age_output = article.age()
        self.assertEqual("2 days", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(days=2, hours=11, minutes=59, seconds=59)).timestamp()
        age_output = article.age()
        self.assertEqual("2 days", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(days=2, hours=12, minutes=0, seconds=1)).timestamp()
        age_output = article.age()
        self.assertEqual("3 days", age_output)

        article.timestamp = (datetime.utcnow() - timedelta(days=2, hours=23, minutes=59, seconds=59)).timestamp()
        age_output = article.age()
        self.assertEqual("3 days", age_output)


if __name__ == '__main__':
    unittest.main()
