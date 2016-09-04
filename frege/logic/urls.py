from django.conf.urls import url

from . import views

app_name = 'logic'
urlpatterns = [

    # general
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
    url(r'^stats/$', views.StatsView.as_view(), name='stats'),
    url(r'^user/$', views.UserView.as_view(), name='user'),

    # content
    url(r'^(?P<chnum>[0-9]+)/$', views.ChapterView.as_view(), name='chapter'),
    url(r'^(?P<chnum>[0-9]+)/stats/$', views.ChapterStatsView.as_view(), name='chapter-stats'),
    url(r'^(?P<chnum>[0-9]+)/summary/$', views.ChapterSummaryView.as_view(), name='chapter-summary'),
    url(r'^(?P<chnum>[0-9]+)/(?P<qnum>[0-9]+)/$', views.QuestionView.as_view(), name='question'),
    url(r'^(?P<chnum>[0-9]+)/(?P<qnum>[0-9]+)/followup/$', views.FollowupQuestionView.as_view(), name='followup'),

    # help
    url(r'^help/$', views.HelpView.as_view(), name='help'),
    url(r'^help/(?P<topic>[0-9]+)/$', views.TopicHelpView.as_view(), name='topic-help'),
    url(r'^help/groups$', views.GroupHelpView.as_view(), name='group-help'),

]
