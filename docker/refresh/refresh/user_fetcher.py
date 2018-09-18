import logging
from datetime import datetime

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from models import User
from db import Session

USER_URL = 'https://hacker-news.firebaseio.com/v0/user/'


def fetch_blacklist():
    ses = Session()
    ids = ses.query(User.id).filter(User.state == 99).all()
    #returned as a list of single value tuples
    return [value for value, in ids]


def fetch_user(username):
    """ Locally and then remotely attempts to load the given user
    :param username:
    :return: user object or none if not found
    """
    if not username:
        logging.info('No username given')
        return None
    if username in fetch_blacklist():
        logging.info('User on blacklist, ' + username)
        return None

    ses = Session()
    user = ses.query(User).filter(User.id == username).first()
    if not user:
        user = fetch_user_remote(username)
    else:
        threshold = datetime.utcnow() - User.refresh_delta
        if user.last_parsed is not None and user.last_parsed < threshold:
            logging.info('User cache expired, ' + username)
            user.state = 11
        elif user.state == 10:
            logging.info('Using cached version of ' + username)

    return user


def fetch_user_remote(username):
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
