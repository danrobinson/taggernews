# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests

from django.shortcuts import render

from django.http import HttpResponse

from models import Article, Tag

from django.db.models import Count


def front_page(request):
  articles = Article.objects.all().order_by('-timestamp')[:30]

  context = {
    "articles": articles
  }

  return render(request, 'article_list.html', context)

def by_tag(request, tag_string):
  tag_names = [tag_name.lower().capitalize() for tag_name in tag_string.split('+')]

  print tag_names

  tags = Tag.objects.filter(name__in=tag_names)

  articles = Article.objects.filter(tags__in=tags)

  context = {
    "articles": articles
  }
  return render(request, 'article_list.html', context)

def all_tags(request):
  
  tags = Tag.objects.annotate(article_count=Count('article')).order_by('-article_count')
                    
  context = {
    "tags": tags
  }

  return render(request, 'tag_list.html', context)
