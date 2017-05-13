# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests

from django.shortcuts import render

from django.http import HttpResponse

from models import Article

MAX_UPDATES = 10 # Per request
TOP_ARTICLES_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%s.json'

def front_page(request):
  articles = Article.objects.all().order_by('-hn_id')

  context = {
      "articles": articles
  }
  return render(request, 'front_page.html', context)

def refresh_top_articles(request):
  top_article_ids = requests.get(TOP_ARTICLES_URL).json()
  print top_article_ids
  
  existing_article_ids = Article.objects \
    .filter(hn_id__in=top_article_ids) \
    .values_list('hn_id', flat=True)
  new_article_ids = list(set(top_article_ids) - set(existing_article_ids))
  
  update_count = 0
  max_updates = int(request.GET.get('max', MAX_UPDATES))
  for article_id in new_article_ids[:max_updates]:
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
    
  return HttpResponse('Added %s articles.' % update_count)
