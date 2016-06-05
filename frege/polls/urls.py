from django.conf.urls import url

from . import views

QID_EXP = '(?P<qid>[0-9]+)'
PK_EXP = '(?P<pk>[0-9]+)'

app_name = 'polls'
urlpatterns = [
    # ex: /polls/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /polls/5/ 
    url(r'^%s/$' % PK_EXP, views.DetailView.as_view(), name='detail'),
    # ex: /polls/5/results/
    url(r'^%s/results/$' % PK_EXP, views.ResultsView.as_view(), name='results'),
    # ex: /polls/5/vote/ 
    url(r'^%s/vote/$' % QID_EXP, views.vote, name='vote'),
]
