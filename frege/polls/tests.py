from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Question

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
