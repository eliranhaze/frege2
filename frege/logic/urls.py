from django.conf.urls import url

from . import views

NUM_EXP = '(?P<number>[0-9]+)'

app_name = 'logic'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^%s/$' % NUM_EXP, views.ChapterView.as_view(), name='chapter'),
]
