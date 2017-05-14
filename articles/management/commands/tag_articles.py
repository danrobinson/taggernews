import random

from django.core.management.base import BaseCommand, CommandError
from goose import Goose
import requests

from articles.models import Article, Tag

TOP_ARTICLES_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'

def predict_tags(prediction_input):
  # Replace with actual data science stuff
  num_tags = random.randint(1, 3)
  some_tags = [
    'Apple', 'Data Science', 'Facebook', 'Tesla', 'Javascript',
    'Startups', 'Politics', 'Google', 'Linux', 'DevOps', 'Design',
  ] 
  tags = random.sample(some_tags, num_tags)
  return tags

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
        goosed_article.cleaned_text.encode('utf-8'),
        goosed_article.meta_description.encode('utf-8'),
      )
      predicted_tags = predict_tags(prediction_input)

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
        
