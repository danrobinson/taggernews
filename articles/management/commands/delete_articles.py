import random

from django.core.management.base import BaseCommand, CommandError
from goose import Goose
import requests

from articles.models import Article

class Command(BaseCommand):
  help = 'Closes the specified poll for voting'

  def handle(self, *args, **options):
    Article.objects.all().delete()
    self.stdout.write(self.style.SUCCESS("Deleted all articles."))
