from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from .models import Question

def create_question(text, days):
     time = timezone.now() + timedelta(days=days)
     return Question.objects.create(text=text, date=time)
 
class QuestionViewTests(TestCase):
 
    def _get(self):
        return self.client.get(reverse('polls:index'))

    def _assertEmpty(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls are available')
        self.assertQuerysetEqual(response.context['qlist'], [])

    def _assertContains(self, response, questions):
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['qlist'],
            [repr(q) for q in questions],
            ordered = False
        )
        
    def test_index_view_no_questions(self):
        """should display message when no questions exists"""
        self._assertEmpty(self._get())

    def test_index_view_future_question(self):
        """should display no future question"""
        create_question('future', days=30)
        self._assertEmpty(self._get())

    def test_index_view_past_question(self):
        """should display past question"""
        q = create_question('past', days=-30)
        self._assertContains(self._get(), [q])

    def test_index_view_past_and_future(self):
        """should display past question"""
        q = create_question('past', days=-30)
        create_question('future', days=30)
        self._assertContains(self._get(), [q])

    def test_index_view_two_past(self):
        """should display past question"""
        q = create_question('past', days=-30)
        q2 = create_question('past2', days=-10)
        self._assertContains(self._get(), [q, q2])

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
