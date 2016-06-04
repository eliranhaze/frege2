from django.conf.urls import url

from . import views

QID_EXP = '(?P<qid>[0-9]+)'

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.index, name='index'),
    # ex: /polls/5/ 
    url(r'^%s/$' % QID_EXP, views.detail, name='detail'),
    # ex: /polls/5/results/
    url(r'^%s/results/$' % QID_EXP, views.detail, name='results'),
    # ex: /polls/5/vote/ 
    url(r'^%s/vote/$' % QID_EXP, views.detail, name='vote'),
]
