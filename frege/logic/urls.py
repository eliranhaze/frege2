from django.conf.urls import url

from . import views

app_name = 'logic'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
    url(r'^user/$', views.UserView.as_view(), name='user'),
    url(r'^help/$', views.HelpView.as_view(), name='help'),
    url(r'^help/(?P<topic>[0-9]+)/$', views.TopicHelpView.as_view(), name='topic-help'),
    url(r'^(?P<chnum>[0-9]+)/$', views.ChapterView.as_view(), name='chapter'),
    url(r'^(?P<chnum>[0-9]+)/summary/$', views.ChapterSummaryView.as_view(), name='chapter-summary'),
    url(r'^(?P<chnum>[0-9]+)/(?P<qnum>[0-9]+)/$', views.QuestionView.as_view(), name='question'),
    url(r'^(?P<chnum>[0-9]+)/(?P<qnum>[0-9]+)/followup/$', views.FollowupQuestionView.as_view(), name='followup'),
]
