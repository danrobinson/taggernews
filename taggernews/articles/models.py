# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from urlparse import urlparse

# Create your models here.

class Tag(models.Model):
  name = models.CharField(max_length=255)

  def __unicode__(self):
    return self.name

class Article(models.Model):
  hn_id = models.IntegerField(primary_key=True)
  title = models.CharField(max_length=255)
  article_url = models.URLField(max_length=255)
  score = models.IntegerField()
  number_of_comments = models.IntegerField()
  submitter = models.CharField(max_length=255)
  age = models.IntegerField()
  tags = models.ManyToManyField(Tag)

  def __unicode__(self):
    return self.title

  def site(self):
    return urlparse(self.article_url).netloc[4:]
