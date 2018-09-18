import time
import logging

def examine_articles(text_tagger, articles, num_articles=50, num_char=200):
    for idx, articletext in enumerate(articles[:num_articles]):
        if len(articletext) >= 20:
            logging.info(idx, articletext[:num_char].replace("\n", ""))
            logging.info(text_tagger.text_to_tags(articletext))
            logging.info()


def make_time_filename(prefix, ext):
    """Creates a filename with the time in it."""
    suffix = time.strftime("_%b%d_%H%M") + ext
    return prefix + suffix
