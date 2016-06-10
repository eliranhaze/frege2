# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils import timezone

# Create your models here.

class Question(models.Model):
    text = models.CharField(max_length=200)
    date = models.DateTimeField('date published')

    def was_published_recently(self):
        now = timezone.now()
        return now > self.date > now - datetime.timedelta(days=1)
    was_published_recently.admin_order_field = 'date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'פורסם לאחרונה?'

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = "שאלה"
        verbose_name_plural = "שאלות"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = 'בחירה'
        verbose_name_plural = 'בחירות'

