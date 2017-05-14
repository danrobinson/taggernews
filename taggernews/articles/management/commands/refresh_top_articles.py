from django.core.management.base import BaseCommand, CommandError
import requests

from articles.models import Article

TOP_ARTICLES_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'

class Command(BaseCommand):
  help = 'Closes the specified poll for voting'

  def add_arguments(self, parser):
    parser.add_argument(
      '--max_articles',
      action='store',
      dest='max_articles',
      default=False,
      help='Specify maximum number of articles to update.',
    )

  def handle(self, *args, **options):
    top_article_ids = requests.get(TOP_ARTICLES_URL).json()
    existing_article_ids = Article.objects \
      .filter(hn_id__in=top_article_ids) \
      .values_list('hn_id', flat=True)
    new_article_ids = list(set(top_article_ids) - set(existing_article_ids))
  
    update_count = 0
    max_articles = options.get('max_articles') or len(new_article_ids)
    for article_id in new_article_ids[:max_articles]:
      article_info = requests.get(ITEM_URL % article_id).json()
    
      Article.objects.create(
        hn_id=article_id,
        title=article_info.get('title'),
        article_url=article_info.get('url'),
        score=article_info.get('score'),
        number_of_comments=article_info.get('descendants'),
        submitter=article_info.get('by'),
        timestamp=article_info.get('time'),
      )
      update_count += 1
      
      if update_count % 10 == 0:
        self.stdout.write(self.style.SUCCESS('Added %s articles...' % update_count))

    self.stdout.write(self.style.SUCCESS('Done. Added %s articles' % update_count))
        