from django.core.management.base import BaseCommand, CommandError
import requests
import sys

from articles.models import Article



TOP_ARTICLES_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'

class Command(BaseCommand):
  help = 'Closes the specified poll for voting'

  def handle(self, *args, **options):
    top_article_ids = requests.get(TOP_ARTICLES_URL).json()
    
    update_count = 0 
    create_count = 0
    for rank, article_id in enumerate(top_article_ids):
      article_info = requests.get(ITEM_URL % article_id).json()
      try:
        article = Article.objects.get(hn_id=article_id)
        article.score = article_info.get('score')
        article.number_of_comments = article_info.get('descendants')
        article.rank = rank
        article.save()
        update_count += 1
      except Article.DoesNotExist:
        try:
          Article.objects.create(
            hn_id=article_id,
            title=article_info.get('title'),
            article_url=article_info.get('url'),
            score=article_info.get('score'),
            number_of_comments=article_info.get('descendants'),
            submitter=article_info.get('by'),
            timestamp=article_info.get('time'),
            rank=rank,
          )
          create_count += 1
        except e:
          sys.stderr.write(str(e))

      
      if rank % 10 == 0:
        message = "Added %s articles, updated %s articles..." % (
          create_count, update_count)
        self.stdout.write(self.style.SUCCESS(message))
    
    Article.objects \
      .exclude(hn_id__in=top_article_ids) \
      .update(rank=None)

    self.stdout.write(self.style.SUCCESS(
      'Done. Added: %s, Updated: %s' % (create_count, update_count)))
        