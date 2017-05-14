from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls import include

from articles.views import news, by_tag, all_tags

urlpatterns = [
  url(r'^$', news),
  url(r'^news/$', news),
  url(r'^news/(?P<page>\d+)$', news),
  url(r'^tags/(?P<tag_string>[A-Za-z\/ ]+(\+[A-Za-z\/ ]+)*)/$', by_tag),
  url(r'^tags/(?P<tag_string>[A-Za-z\/ ]+(\+[A-Za-z\/ ]+)*)/(?P<page>\d+)$', by_tag),
  url(r'^tags/$', all_tags),
  url(r'^admin/', admin.site.urls)
]

if settings.DEBUG:
  import debug_toolbar
  urlpatterns = [
    url(r'^__debug__/', include(debug_toolbar.urls)),
  ] + urlpatterns
