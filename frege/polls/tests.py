from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from .models import Question

def create_question(text, days):
    time = timezone(now) + timedelta(days=days)
    return Question.objects.create(text=text, date=time)

class QuestionViewTests(TestCase):

    def test_index_view_no_questions(self):
        """ should display message when no questions exists"""
        res = self.client.get(reverse('polls:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'No polls are available')
        self.assertQuerysetEqual(res.context['qlist'], [])

class QuestionTests(TestCase):

    def test_was_published_recently_future(self):
        """should return false for future questions"""
        fut = Question(date=timezone.now() + timedelta(days=3))
        self.assertEqual(fut.was_published_recently(), False)

    def test_was_published_recently_old(self):
        """should return false for older than 1-day questions"""
        old = Question(date=timezone.now() - timedelta(days=2))
        self.assertEqual(old.was_published_recently(), False)

    def test_was_published_recently_recent(self):
        """should return true for within last 1-day questions"""
        old = Question(date=timezone.now() - timedelta(hours=2))
        self.assertEqual(old.was_published_recently(), True)
