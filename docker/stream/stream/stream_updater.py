import logging
import firebase
from datetime import datetime


from article_fetcher import ArticleFetcher

COMMENT_URL = "https://hacker-news.firebaseio.com/v0/updates.json"


class StreamUpdater:

    def __init__(self):
        self.arty = ArticleFetcher()

    def add(self, stream_text):
        message = stream_text[1]
        logging.info(datetime.now())
        logging.info('Data: ' + str(message))
        items = message['data']['items']
        items = self.arty.fetch_list(items)
        logging.info('Completed fetch of ' + str(len(items)))

print("Starting StreamUpdater")
updater = StreamUpdater()
comment_sub = firebase.subscriber(COMMENT_URL, updater.add)
comment_sub.start()
print("StreamUpdater waiting for push")
