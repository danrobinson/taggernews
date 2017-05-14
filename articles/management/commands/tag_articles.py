import pickle
import random

from django.core.management.base import BaseCommand, CommandError
from gensim import corpora, models
from goose import Goose
import nltk
from nltk import word_tokenize
import numpy as np
import requests

from articles.models import Article, Tag

nltk.download('punkt')

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
    tokens = word_tokenize(text)
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
    with open(lr_dict_fname, "rb") as f:
      lr_dict = pickle.load(f)
    return cls(topic_modeler, gensim_dict, lr_dict, *args, **kwargs)
    

text_tagger = TextTagger.init_from_files(
  "articles/model/model_100topics_10passMay13_2159.gensim", 
  "articles/model/hn_dictionaryMay13_2152.pkl", 
  "articles/model/logistic_models_May14_0015.pkl", 
  threshold=0.2,
)

class Command(BaseCommand):
  help = 'Closes the specified poll for voting'

  def handle(self, *args, **options):
    articles = Article.objects.filter(
      tagged=False, article_url__isnull=False)
    
    goose = Goose()
    for i, article in enumerate(articles):
      # Get article content
      try:
        goosed_article = goose.extract(url=article.article_url)                
      except Exception:
        self.stdout.write(self.style.ERROR(
          'Failed to get article %s content.' % article.hn_id))
        continue
       
      # Make tag predictions
      prediction_input = '%s|||\n\n%s' % (
        goosed_article.cleaned_text,
        goosed_article.meta_description,
      )
      prediction_input = prediction_input.encode('utf-8')
      predicted_tags = text_tagger.text_to_tags(prediction_input)

      # Add tags to db (only matters if there's a previously unseen tag)
      existing_tags = Tag.objects.filter(name__in=predicted_tags)
      new_tags = set(predicted_tags) - set([t.name for t in existing_tags])
      new_tags = Tag.objects.bulk_create([Tag(name=t) for t in new_tags])
      
      # Associate tags with article (many-to-many)
      article_tags = list(existing_tags) + new_tags
      article_tags = Tag.objects.filter(id__in=[t.id for t in article_tags])
      article.tags.add(*article_tags)
      
      article.tagged = True
      article.save()
        
      self.stdout.write(self.style.SUCCESS(
        'Tagged article %s (%s of %s)' % (
        article.hn_id, i + 1, articles.count())
      ))
