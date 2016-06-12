from django.conf.urls import url

from . import views

PK_EXP = '(?P<pk>[0-9]+)'

app_name = 'logic'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^%s/$' % PK_EXP, views.ChapterView.as_view(), name='chapter'),
]
