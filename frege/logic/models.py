# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from django.db.models.signals import post_delete 
from django.dispatch import receiver

from .formula import (
    Formula,
    FormulaSet,
    Argument,
    formal_type,
)

import logging
logger = logging.getLogger(__name__)

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

def shorten_text(text, size=50):
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

    def first_question(self):
        return min(self.questions(), key=lambda q: q.number)

    def __unicode__(self):
        return '%s. %s' % (self.number, self.title)

    class Meta:
        verbose_name = 'פרק'
        verbose_name_plural = 'פרקים'
        ordering = ['number']

class Question(models.Model):

    DEFAULT_NUM = 0

    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    number = models.PositiveIntegerField(default=DEFAULT_NUM, verbose_name='מספר')

    def user_answers(self):
        return UserAnswer.objects.filter(chapter=self.chapter, question_number=self.number)
    
    def user_answer(self, user):
        return UserAnswer.objects.filter(user=user, chapter=self.chapter, question_number=self.number)

    def clean(self):
        # TODO: does this have unit tests? it should
        super(Question, self).clean()
        if self.chapter_id and self.number > 0: # TODO: probably add condition for followup question with the same number
            chapter_questions = Question._filter(chapter=self.chapter)
            if self.number in set([q.number for q in Question._filter(chapter=self.chapter) if q.id != self.id]):
                raise ValidationError({'number':'כבר קיימת שאלה מספר %d בפרק זה' % (self.number)})

    def save(self, *args, **kwargs):
        logger.debug('saving %s', self)
        if self.number == self.DEFAULT_NUM:
            # set a number for this question
            others = Question._filter(chapter=self.chapter)
            self.number = max(q.number for q in others) + 1 if others else 1
            logger.debug('setting number to %d', self.number)
        self.clean()
        super(Question, self).save(*args, **kwargs)

    def has_followup(self):
        return self.__class__ == FormulationQuestion and self.followup != FormulationQuestion.NONE

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
        ordering = ['number']

@receiver(post_delete)   
def delete_stuff(instance, sender, **kwargs):
    # do stuff upon question deletion
    if issubclass(sender, Question):
        self = instance
        logger.debug('post delete %s', self)
        # delete question-related entities
        for ua in self.user_answers():
            logger.debug('deleting %s of question %s', ua, self)
            ua.delete()
        # re-order other questions
        for q in Question._filter(chapter=self.chapter, number__gt=self.number):
            q.number = q.number - 1
            q.save()
            logger.debug('reordered %s', q)

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

    def __unicode__(self):
        return '%s. %s' % (self.number, self.formula)

    class Meta(Question.Meta):
        abstract = True

class FormulationQuestion(TextualQuestion):
    NONE = 'N'
    TRUTH_TABLE = 'T'
    DEDUCTION = 'D'
    FOLLOWUP_CHOICES = (
        (NONE, 'ללא'),
        (TRUTH_TABLE,'טבלת אמת'),
        (DEDUCTION, 'דדוקציה'),
    )
    followup = models.CharField(verbose_name='שאלת המשך',max_length=1,choices=FOLLOWUP_CHOICES,default=NONE)

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

def validate_formula(formula):
    try:
        return Formula(formula).literal
    except:
        raise ValidationError({'formula':'הנוסחה שהוזנה אינה תקינה'})

def validate_formula_set(fset):
    try:
        return FormulaSet(fset).literal
    except:
        raise ValidationError({'formula':'הקבוצה שהוזנה אינה תקינה'})

def validate_argument(arg):
    try:
        return Argument(arg).literal
    except:
        msg = 'הטיעון שהוזן אינו תקין'
        raise ValidationError({'formula':msg})

def validate_deduction_argument(arg):
    try:
        a = Argument(arg)
    except:
        raise ValidationError({'formula':'הטיעון שהוזן אינו תקין'})
    if not a.is_valid:
        raise ValidationError({'formula':'הטיעון שהוזן אינו ניתן להוכחה'})
    return a.literal

def validate_truth_table(x):
    pass

class TruthTableQuestion(FormalQuestion):
    FORMULA = 'F'
    SET = 'S'
    ARGUMENT = 'A'
    TABLE_CHOICES = (
        (FORMULA, 'נוסחה'),
        (SET,'קבוצה'),
        (ARGUMENT, 'טיעון'),
    )
    table_type = models.CharField(verbose_name='סוג',max_length=1,choices=TABLE_CHOICES)
    formula = models.CharField(verbose_name='נוסחה/טיעון/קבוצה', max_length=60)

    @property
    def options(self):
        if self.is_formula:
            return FORMULA_OPTIONS
        elif self.is_set:
            return SET_OPTIONS
        elif self.is_argument:
            return ARGUMENT_OPTIONS

    @property
    def is_formula(self):
        return self.table_type == self.FORMULA
 
    @property
    def is_set(self):
        return self.table_type == self.SET
 
    @property
    def is_argument(self):
        return self.table_type == self.ARGUMENT
 
    def clean(self):
        super(TruthTableQuestion, self).clean()
        self._set_table_type()
        if self.is_formula:
            self.formula = validate_formula(self.formula)
        elif self.is_set:
            self.formula = validate_formula_set(self.formula)
        elif self.is_argument:
            self.formula = validate_argument(self.formula)

    def save(self, *args, **kwargs):
        self._set_table_type()
        super(TruthTableQuestion, self).save(*args, **kwargs)

    def display(self):
        if self.is_formula:
            return self.formula
        if self.is_set:
            return FormulaSet(self.formula).display
        if self.is_argument:
            return Argument(self.formula).display

    def _set_table_type(self):
        if not self.table_type:
            self.table_type = {
                Formula: self.FORMULA,
                FormulaSet: self.SET,
                Argument: self.ARGUMENT
            }[formal_type(self.formula)]

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת טבלת אמת'
        verbose_name_plural = 'שאלות טבלת אמת'
        unique_together = ('chapter', 'formula')

class DeductionQuestion(FormalQuestion):
    formula = models.CharField(verbose_name='טיעון', max_length=60)

    def clean(self):
        super(DeductionQuestion, self).clean()
        self.formula = validate_deduction_argument(self.formula)

    def display(self):
        return Argument(self.formula).display

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת דדוקציה'
        verbose_name_plural = 'שאלות דדוקציה'
        unique_together = ('chapter', 'formula')

class FormulationAnswer(models.Model):
    formula = models.CharField(verbose_name='נוסחה', max_length=60)
    question = models.ForeignKey(FormulationQuestion, verbose_name='שאלה', on_delete=models.CASCADE)

    def clean(self):
        super(FormulationAnswer, self).clean()
        ftype = formal_type(self.formula)
        if ftype == Formula:
            self.formula = validate_formula(self.formula)
        elif ftype == FormulaSet:
            self.formula = validate_formula_set(self.formula)
        elif ftype == Argument:
            self.formula = validate_argument(self.formula)
        # TODO: if formula is FOL, followup must not be truth table

    def __unicode__(self):
        return self.formula

    class Meta:
        verbose_name = 'תשובה'
        verbose_name_plural = 'תשובות'

class Choice(models.Model):
    text = models.CharField(verbose_name='טקסט', max_length=200)
    question = models.ForeignKey(ChoiceQuestion, verbose_name='שאלה', on_delete=models.CASCADE)
    is_correct = models.BooleanField(verbose_name='תשובת נכונה?', default=False)

    @property
    def short_text(self):
        return shorten_text(self.text)

    def __unicode__(self):
        return self.short_text

    class Meta:
        verbose_name = 'בחירה'
        verbose_name_plural = 'בחירות'

class ChapterSubmission(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    attempt = models.PositiveIntegerField(verbose_name='נסיונות')
    ongoing = models.BooleanField()
    time = models.DateTimeField(verbose_name='זמן הגשה', blank=True, null=True)

    def is_complete(self):
        return self.chapter.num_questions() == len(UserAnswer.objects.filter(chapter=self.chapter))

    @property
    def max_attempts(self):
        return 3

    def can_try_again(self):
        return self.attempt < self.max_attempts

    @property
    def percent_correct_f(self):
        return self.percent_correct()

    def percent_correct(self):
        user_answers = UserAnswer.objects.filter(user=self.user, chapter=self.chapter)
        num_correct = sum(1 for u in user_answers if u.correct)
        return int(round(num_correct * 100. / self.chapter.num_questions()))
    percent_correct.short_description = 'ציון'

    @property
    def chapter_number_f(self):
        return self.chapter.number

    def chapter_number(self):
        return self.chapter.number
    chapter_number.short_description = 'פרק'

    def __unicode__(self):
        return '%s/%s' % (self.user, self.chapter.number)

    class Meta:
        verbose_name = 'הגשת משתמש'
        verbose_name_plural = 'הגשות משתמשים'
        unique_together = ('chapter', 'user')
        ordering = ['chapter']

class UserAnswer(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    submission = models.ForeignKey(ChapterSubmission, verbose_name='הגשת פרק', on_delete=models.CASCADE)
    question_number = models.PositiveIntegerField(verbose_name='מספר שאלה')
    correct = models.BooleanField(verbose_name='תשובה נכונה')
    answer = models.TextField()
    is_followup = models.BooleanField(default=False)
    time = models.DateTimeField(verbose_name='זמן', blank=True, null=True)

    def __unicode__(self):
        return '%s/%s/%s/%s' % (self.user, self.chapter.number, self.question_number, 'T' if self.correct else 'F')

    class Meta:
        verbose_name = 'תשובת משתמש'
        verbose_name_plural = '*תשובות משתמשים'
        unique_together = ('chapter', 'user', 'question_number', 'is_followup')

