import traceback
import logging
import requests

from models import User, Item

ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'


class CommentFetcher:
    STAT_ITEM_FROM_HN = 0
    STAT_USER_CREATED = 0
    STAT_ITEM_CREATED = 0

    def __init__(self):
        pass

    def fetch(self, top_parent, comment_ids):
        self._fetch(None, top_parent, comment_ids)

    def _fetch(self, parent, top_parent, comment_ids):
        hn_id = parent.hn_id if parent else top_parent.hn_id
        logging.info('Fetching %s children for %s' % (str(len(comment_ids)), str(hn_id)))
        for cid in comment_ids:
            try:
                article_info = requests.get(ITEM_URL % cid).json()
                self.STAT_ITEM_FROM_HN += 1
                submitter_id = article_info.get('by')
                if submitter_id is None:
                    submitter_id = 'deleted'
                submitter, created = User.objects.get_or_create(id=submitter_id)
                if created:
                    self.STAT_USER_CREATED += 1

                item, created = Item.objects.get_or_create(
                    hn_id=cid,
                    submitter=submitter,
                    type=article_info.get('type'),
                    parent=parent,
                    top_parent=top_parent
                )

                if created:
                    logging.info('Created item: ' + str(cid))
                    self.STAT_ITEM_CREATED += 1
                else:
                    logging.info('Existing item: ' + str(cid))
                kids = article_info.get('kids')
                if kids:
                    self._fetch(item, top_parent, kids)

            except Exception as e:
                traceback.print_exc(e)
