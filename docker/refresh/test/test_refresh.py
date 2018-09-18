import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from refresh import dbconn_test
from refresh.refresh import refresh_top


class TestArticleFetcher(unittest.TestCase):

    engine = create_engine(dbconn_test)
    Session = sessionmaker(bind=engine)

    def setUp(self):
        self.ses = self.Session()

    def test_smoke(self):
        refresh_top()

    def test_front_page_user_priority_escalation(self):
        """
            A user that lands on the front page should be queued for
            parsing
        """
        pass

if __name__ == '__main__':
    unittest.main()
