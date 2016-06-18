# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

"""
This module contains definitions for the app's entities.

Here's a brief summary:
- Chapter: a group of questions that has a number and title.
- OpenQuestion: a question with no predifined answer.
- ChoiceQuestion: a question with several choices (some of them correct).
- FormulationQuestion: a question with predefined answers (all of them correct).
- TruthTableQuestion: a question that is answered by a truth table in gui.
- DeductionQuestion: a question that is answered by a deduction in gui.
"""

def shorten_text(text, size=40):
    return text if len(text) <= size else '%s...' % text[:size-3]

def _concrete_sub_classes(cls):
    subs = []
    for sub in cls.__subclasses__():
        if sub._meta.abstract:
            subs.extend(_concrete_sub_classes(sub))
        else:
            subs.append(sub)
    return subs
         
class Chapter(models.Model):
    number = models.PositiveIntegerField(verbose_name='מספר', unique=True)
    title = models.CharField(verbose_name='כותרת', max_length=30)

    def num_questions(self):
        return Question._count(chapter__number=self.number)
    num_questions.short_description = 'מספר שאלות'

    def questions(self):
        return Question._filter(chapter__number=self.number)

    def __unicode__(self):
        return '%s. %s' % (self.number, self.title)

    class Meta:
        verbose_name = 'פרק'
        verbose_name_plural = 'פרקים'
        ordering = ['number']

class Question(models.Model):
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    followup = models.ForeignKey('self', verbose_name='שאלת המשך', on_delete=models.CASCADE, blank=True, null=True)
    number = models.PositiveIntegerField(verbose_name='מספר')

    def user_answers(self):
        return UserAnswer.objects.filter(chapter=self.chapter, question_number=self.number)
    
    def user_answer(self, user):
        return UserAnswer.objects.filter(user=user, chapter=self.chapter, question_number=self.number)
    
    @classmethod
    def _all(cls):
        return cls._sub_func('all')

    @classmethod
    def _filter(cls, **kwargs):
        return cls._sub_func('filter', **kwargs)

    @classmethod
    def _get(cls, **kwargs):
        result = cls._filter(**kwargs)
        if not result:
            return None
        assert len(result) == 1
        return result[0]
 
    @classmethod
    def _count(cls, **kwargs):
        return len(cls._filter(**kwargs))

    @classmethod
    def _sub_func(cls, func_name, **kwargs):
        concretes = _concrete_sub_classes(cls)
        all_obj = []
        for c in concretes:
            all_obj.extend(getattr(c.objects, func_name)(**kwargs))
        return all_obj

    class Meta:
        abstract = True
        # this is insufficient since it is enforced on a table level only so
        # i can e.g. get deduction and open question with the same number and chapter
        # so... TODO: custom validation
        unique_together = ('chapter', 'number')
        ordering = ['number']

class TextualQuestion(Question):
    text = models.TextField(verbose_name='טקסט')

    @property
    def short_text(self):
        return shorten_text(self.text)
 
    def __unicode__(self):
        return '%s. %s' % (self.number, self.short_text)

    class Meta(Question.Meta):
        abstract = True

class FormalQuestion(Question):
    formula = models.CharField(verbose_name='נוסחה', max_length=30)

    def __unicode__(self):
        return '%s. %s' % (self.number, self.formula)

    class Meta(Question.Meta):
        abstract = True

class FormulationQuestion(TextualQuestion):

    class Meta(TextualQuestion.Meta):
        verbose_name = 'שאלת הצרנה'
        verbose_name_plural = 'שאלות הצרנה'

class OpenQuestion(TextualQuestion):

    class Meta(TextualQuestion.Meta):
        verbose_name = 'שאלת פתוחה'
        verbose_name_plural = 'שאלות פתוחות'

class ChoiceQuestion(TextualQuestion):

    class Meta(TextualQuestion.Meta):
        verbose_name = 'שאלת בחירה'
        verbose_name_plural = 'שאלות בחירה'

class TruthTableQuestion(FormalQuestion):

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת טבלת אמת'
        verbose_name_plural = 'שאלות טבלת אמת'

class DeductionQuestion(FormalQuestion):
    premises = models.CharField(verbose_name='הנחות', max_length=300)
    # TODO: list? see: http://stackoverflow.com/questions/22340258/django-list-field-in-model
    # TODO: also, this should be optional (e.g. theorems)

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת דדוקציה'
        verbose_name_plural = 'שאלות דדוקציה'
DeductionQuestion._meta.get_field('formula').verbose_name = 'מסקנה'

class Answer(models.Model):
    text = models.CharField(verbose_name='טקסט', max_length=200)

    @property
    def short_text(self):
        return shorten_text(self.text)

    def __unicode__(self):
        return self.short_text

    class Meta:
        abstract = True

class FormulationAnswer(Answer):
    question = models.ForeignKey(FormulationQuestion, verbose_name='שאלה', on_delete=models.CASCADE)

    class Meta(Answer.Meta):
        verbose_name = 'תשובה'
        verbose_name_plural = 'תשובות'

class Choice(Answer):
    question = models.ForeignKey(ChoiceQuestion, verbose_name='שאלה', on_delete=models.CASCADE)
    is_correct = models.BooleanField(verbose_name='תשובת נכונה?', default=False)

    class Meta(Answer.Meta):
        verbose_name = 'בחירה'
        verbose_name_plural = 'בחירות'

class UserAnswer(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    question_number = models.PositiveIntegerField(verbose_name='מספר שאלה')
    # TODO: since  there is no fk to question here, deleting question won't cause deleting this,
    # so i must take care of that myself.
    correct = models.BooleanField(verbose_name='תשובה נכונה')

    def __unicode__(self):
        return 'UserAnswer: %s/%s/%s/%s' % (self.user, self.chapter.number, self.question_number, self.correct)

    class Meta(Answer.Meta):
        verbose_name = 'תשובת משתמש'
        verbose_name_plural = 'תשובות משתמש'
        unique_together = ('chapter', 'user', 'question_number')

