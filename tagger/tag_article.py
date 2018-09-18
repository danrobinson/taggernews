import glob
import os
import numpy as np
import time
import logging

from django.core.wsgi import get_wsgi_application
from django.db import transaction
from gensim import corpora, models, utils
from sklearn.externals import joblib
from whitenoise.django import DjangoWhiteNoise

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    application = get_wsgi_application()
    application = DjangoWhiteNoise(application)
from tagger import settings
from tagger.models import Article, Tag

ARTICLE_EXHAUSTION_SLEEP = 30
LIMIT_RESOURCES = False

class TextTagger(object):
    """Object which tags articles. Needs topic modeler and """

    def __init__(self, topic_modeler, gensim_dict, lr_dict, threshold=0.5):
        super(TextTagger, self).__init__()
        self.topic_modeler = topic_modeler
        self.gensim_dict = gensim_dict
        self.lr_dict = lr_dict
        self.threshold = threshold

    def text_to_topic_list(self, text):
        text = text.lower()
        tokens = list(utils.tokenize(text))
        bow = self.gensim_dict.doc2bow(tokens)
        return self.topic_modeler[bow]

    def text_to_numpy(self, text):
        out = np.zeros(self.topic_modeler.num_topics)
        for idx, val in self.text_to_topic_list(text):
            out[idx] = val
        return out

    def text_to_topic_dict(self, text):
        return {topic: weight for topic, weight in self.label_article(text)}

    def text_to_tags(self, text):
        input_vect = np.array([self.text_to_numpy(text)])
        tags = []
        for label, lr_model in self.lr_dict.items():
            tag_prob = lr_model.predict_proba(input_vect)[0, 1]
            if tag_prob > self.threshold:
                tags.append(label)

        return tags

    @classmethod
    def init_from_files(cls, topic_model_fname, gensim_dict_fname, lr_dict_fname,
                        *args, **kwargs):
        topic_modeler = models.ldamodel.LdaModel.load(topic_model_fname)
        gensim_dict = corpora.Dictionary.load(gensim_dict_fname)
        lr_dict = joblib.load(lr_dict_fname)
        return cls(topic_modeler, gensim_dict, lr_dict, *args, **kwargs)


def tag_away(text_tagger, article):
    try:
        articletext = article.articletext.text
        if articletext is None:
            logging.info('No prediction_input for ' + article.hn_id + ', state: ' + article.state)
            article.state = 4
            article.save()
            return 0

        # Make tag predictions
        articletext = articletext.encode('utf-8')
        predicted_tags = text_tagger.text_to_tags(articletext)

    except Exception as e:
        logging.info('Failed to tag article %s. Error: %s.' % (article.hn_id, e))
        article.state = 12
        article.save()
        return

    if len(predicted_tags) == 0:
        article.state = 11
        article_tags = []
    else:
        # Add tags to db (only matters if there's a previously unseen tag)
        existing_tags = Tag.objects.filter(name__in=predicted_tags)
        new_tags = set(predicted_tags) - set([t.name for t in existing_tags])
        new_tags = Tag.objects.bulk_create([Tag(name=t, lowercase_name=t.lower()) for t in new_tags])

        # Associate tags with article (many-to-many)
        article_tags = list(existing_tags) + new_tags
        article_tags = Tag.objects.filter(id__in=[t.id for t in article_tags])
        article.tags.add(*article_tags)

        article.state = 10

    article.save()
    logging.info('Tagged article %s \n%s' % (article.hn_id, article_tags))
    return 1


def latest_resources():
    topic_model = max(glob.iglob(settings.BASE_DIR + '/ml_models/generated/model_*topics_*pass*.gensim'))
    dictionary = max(glob.iglob(settings.BASE_DIR + '/dictionaries/hn_dictionary*.pkl'))
    lr_dictionary = max(glob.iglob(settings.BASE_DIR + '/ml_models/predictions/randomforest_model_*.pkl'))
    return topic_model, dictionary, lr_dictionary


def tag_list(articles):
    topic_model, dictionary, lr_dictionary = latest_resources()
    text_tagger = TextTagger.init_from_files(topic_model, dictionary, lr_dictionary, threshold=0.3)
    logging.info('Loaded resources, created tagger')
    total_count = 0
    for article in articles:
        tag_away(text_tagger, article)
        total_count += 1
    logging.info('Finished after tagging %s articles' % total_count)


def tag(infinite=False):
    topic_model, dictionary, lr_dictionary = latest_resources()
    text_tagger = TextTagger.init_from_files(topic_model, dictionary, lr_dictionary, threshold=0.3)
    logging.info('Loaded resources, created tagger')

    if LIMIT_RESOURCES:
        select_size = 2
        os.nice(20)
    else:
        select_size = 10

    total_count = 0
    while True:
        batch = []
        with transaction.atomic():
            articles = Article.objects.select_for_update()\
                                        .filter(state=0)\
                                        .filter(tagged=False)\
                                        .order_by('-rank')\
                                        [:select_size]
            for article in articles:
                article.state = 13
                article.save()
                batch.append(article.hn_id)

        if len(batch) == 0:
            logging.info('No more articles to tag')
            if infinite:
                time.sleep(ARTICLE_EXHAUSTION_SLEEP)
                logging.info('Sleeping... tagged so far: ' + str(total_count))
            else:
                break
        else:
            logging.info('Loaded batch of ' + str(len(batch)))
            for hn_id in batch:
                article = Article.objects.get(hn_id=hn_id)
                if article and article.state == 13:
                    tag_away(text_tagger, article)
                    total_count += 1
                    if LIMIT_RESOURCES:
                        time.sleep(1)
        logging.info('Completed, checking for more...')

    logging.info('Finished after tagging %s articles' % total_count)

if __name__ == "__main__":
    tag(True)
