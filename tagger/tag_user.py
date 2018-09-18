import sys
import os
import traceback
import time
import requests
import logging
from datetime import timedelta
from cachetools import TTLCache
from django.core.wsgi import get_wsgi_application
from django.db import transaction
from whitenoise.django import DjangoWhiteNoise
from django.utils import timezone

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    application = get_wsgi_application()
    application = DjangoWhiteNoise(application)
# Needs to be imported after django
from tagger.models import Article, User, Item
from tagger.article_fetcher import ArticleFetcher
from tagger.tag_article import tag_list

USER_URL = 'https://hacker-news.firebaseio.com/v0/user/'
USER_REFRESH_DELTA = timedelta(days=100)

cache = TTLCache(maxsize=100, ttl=600)
arty = ArticleFetcher()
black_list = list(User.objects.filter(state=9).values_list('id', flat=True))
black_list.append('deleted')


def refresh_user(user):
    user.articles = Article.objects.all().filter(submitter=user)
    user.items = Item.objects.all().filter(submitter=user)


class UserTagger:
    BATCH_SIZE = 50
    tagged_users = 0

    def __init__(self):
        pass

    def tag(self, username):
        logging.info('Tagging ' + username)

        # user = User.objects.get(id=username)
        user = fetch_user(username)
        if not user:
            return
        user_info = requests.get(USER_URL + username + '.json').json()
        if not user_info:
            user.state = 1
        else:
            to_fetch = []
            for item_str in user_info['submitted']:
                user.total_items += 1
                item_id = int(item_str)
                if not user.has_cached(item_id):
                    # havent found our id in the db, must be new
                    to_fetch.append(item_id)
            if to_fetch:
                to_fetch = to_fetch[:100]  # Limit fetching to speed things up
                logging.info('Fetching ' + str(len(to_fetch)) + ' items for user ' + username)
                arty.fetch(to_fetch)
                refresh_user(user)
                self.tagged_users += 1
            else:
                logging.info(username + ' needed no update')

            user.last_parsed = timezone.now()
            user.priority = None
            user.state = 10

        user.save()

        logging.info('Finished tagging user ' + user.id)

    def tag_job(self, infinite=False):
        while True:
            try:
                user = None
                username = None
                with transaction.atomic():
                    user = User.objects.select_for_update() \
                        .filter(state=0)\
                        .exclude(priority__isnull=True) \
                        .order_by('priority') \
                        .first()
                    if user is None:
                        user = User.objects.select_for_update() \
                            .filter(state=0)\
                            .filter(priority=None) \
                            .first()
                    if user:
                        user.state = 13
                        user.save()
                        username = user.id

                if user:
                    self.tag(username)
                else:
                    logging.info('No users left to tag')
                    if infinite:
                        logging.info('Sleeping...')
                        time.sleep(10)
                    else:
                        logging.info("Quitting...")
                        break
                logging.info('Total users tagged: ' + str(self.tagged_users) + '\n')
            except Exception as e:
                traceback.print_exc(e)
                if username:
                    try:
                        with transaction.atomic():
                            user = User.objects.select_for_update().filter(id=username).first()
                            if user:
                                user.state = 5
                                user.save()
                    except Exception as e:
                        logging.info('And again...')
                        traceback.print_exc(e)
                time.sleep(5)


def _fetch_user_remote(username):
    try:
        user_info = requests.get(USER_URL + username + '.json').json()
        if not user_info:
            logging.info('User doesn\'t exist, ' + username)
            return None
        logging.info('Creating user, ' + username)
        user = User(id=username, state=0, last_parsed=None)
        user.save()
        return user
    except Exception:
        logging.error("Unable to contact api")
        return None


def fetch_user(username):
    """ Locally and then remotely attempts to load the given user
    :param username:
    :return: user object or none if not found
    """
    if not username:
        logging.info('No username given')
        return None
    if username in black_list:
        logging.info('User on blacklist, ' + username)
        return None

    try:
        user = User.objects.filter(id=username).prefetch_related('article_set').prefetch_related('item_set').first()
        if not user:
            user = _fetch_user_remote(username)
        else:
            threshold = timezone.now() - USER_REFRESH_DELTA
            if user.last_parsed is not None and user.last_parsed < threshold:
                logging.info('User cache expired, ' + username)
                user.state = 11
            elif user.state == 10:
                logging.info('Using cached version of ' + username)
            user.save()
    except User.DoesNotExist:
        user = _fetch_user_remote(username)

    return user


def tag_user(username, force_tagging=False):
    """Returns failure code and message or success and tags"""
    logging.info('Fetching user ' + username)
    user = fetch_user(username)
    if user and user.last_parsed is not None:
        if username in cache:
            logging.info('Fetching from cache')
            tags = cache[username]
        else:
            logging.info('Tagging...')
            tags = user.get_tags()
            cache[username] = tags

        if len(tags) == 0:
            return 204, {}
        return 200, tags
    elif not user:
        return 404, {'message': 'User unavailable'}
    elif force_tagging:
        logging.info('Forced tagging...may be some time')
        UserTagger().tag(user.id)
        user.refresh_from_db()
        articles = user.all_articles()
        tag_list(articles)
        user.refresh_from_db()
        tags = user.get_tags()
        return 200, tags
    else:
        user.priority = 1
        user.save()
        return 200, {'message': 'User not yet parsed, check back soon'}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            success, result = tag_user(str(arg), True)
            logging.info(success, result)
    else:
        UserTagger().tag_job(True)
