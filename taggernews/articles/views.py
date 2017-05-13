# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from django.http import HttpResponse

from models import Article


def front_page(request):
  articles = Article.objects.all().order_by('-hn_id')

  context = {
      "articles": articles
  }
  return render(request, 'front_page.html', context)