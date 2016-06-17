from django.conf.urls import url

from . import views

app_name = 'logic'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
    url(r'^(?P<chnum>[0-9]+)/$', views.ChapterView.as_view(), name='chapter'),
    url(r'^(?P<chnum>[0-9]+)/summary/$', views.ChapterSummaryView.as_view(), name='chapter-summary'),
    url(r'^(?P<chnum>[0-9]+)/(?P<qnum>[0-9]+)/$', views.QuestionView.as_view(), name='question'),
]
