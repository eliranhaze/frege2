# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from django.db.models.signals import pre_delete 
from django.dispatch import receiver

from .formula import (
    Formula,
    FormulaSet,
    Argument,
)

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

    def clean(self):
        super(Question, self).clean()
        if self.chapter_id:
            chapter_questions = Question._filter(chapter=self.chapter)
            if self.number in [q.number for q in Question._filter(chapter=self.chapter) if q.id != self.id]:
                raise ValidationError({'number':'כבר קיימת שאלה מספר %d בפרק זה' % (self.number)})

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

@receiver(pre_delete)   
def delete_stuff(instance, sender, **kwargs):
    # delete question-related entities upon question deletion
    if issubclass(sender, Question):
        self = instance
        for ua in self.user_answers():
            ua.delete()

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
        raise ValidationError('הטיעון שהוזן אינו תקין')
    if not a.is_valid:
        raise ValidationError('הטיעון שהוזן אינו ניתן להוכחה')
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
    table_type = models.CharField(verbose_name='סוג',max_length=1,choices=TABLE_CHOICES,default=FORMULA)
    formula = models.CharField(verbose_name='טקסט', max_length=60)

    @property
    def options(self):
        if self.table_type == TruthTableQuestion.FORMULA:
            return FORMULA_OPTIONS
        elif self.table_type == TruthTableQuestion.SET:
            return SET_OPTIONS
        elif self.table_type == TruthTableQuestion.ARGUMENT:
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
        if self.table_type == self.FORMULA:
            self.formula = validate_formula(self.formula)
        elif self.table_type == self.SET:
            self.formula = validate_formula_set(self.formula)
        elif self.table_type == self.ARGUMENT:
            self.formula = validate_argument(self.formula)

    def display(self):
        if self.is_formula:
            return self.formula
        if self.is_set:
            return FormulaSet(self.formula).display
        if self.is_argument:
            return Argument(self.formula).display

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת טבלת אמת'
        verbose_name_plural = 'שאלות טבלת אמת'
        unique_together = ('chapter', 'formula')

class DeductionQuestion(FormalQuestion):
    formula = models.CharField(verbose_name='טיעון', max_length=60, validators=[validate_deduction_argument])

    def clean(self):
        super(DeductionQuestion, self).clean()
        self.formula = validate_argument(self.formula)

    def display(self):
        return Argument(self.formula).display

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת דדוקציה'
        verbose_name_plural = 'שאלות דדוקציה'
        unique_together = ('chapter', 'formula')

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

class UserChapter(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)

    @property
    def percent_correct_f(self):
        return self.percent_correct()

    def percent_correct(self):
        user_answers = UserAnswer.objects.filter(user=self.user, chapter=self.chapter)
        num_correct = sum(1 for u in user_answers if u.correct)
        return num_correct * 100. / self.chapter.num_questions()
    percent_correct.short_description = 'ציון'

    @property
    def chapter_number_f(self):
        return self.chapter.number

    def chapter_number(self):
        return self.chapter.number
    chapter_number.short_description = 'פרק'

    def __unicode__(self):
        return '%s/%s' % (self.user, self.chapter.number)

    class Meta(Answer.Meta):
        verbose_name = 'פתרון משתמש'
        verbose_name_plural = '*פתרונות משתמשים'
        unique_together = ('chapter', 'user')

class UserAnswer(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE)
    user_chapter = models.ForeignKey(UserChapter, verbose_name='פתרון פרק', on_delete=models.CASCADE)
    question_number = models.PositiveIntegerField(verbose_name='מספר שאלה')
    correct = models.BooleanField(verbose_name='תשובה נכונה')

    def __unicode__(self):
        return '%s/%s/%s/%s' % (self.user, self.chapter.number, self.question_number, 'T' if self.correct else 'F')

    class Meta(Answer.Meta):
        verbose_name = 'תשובת משתמש'
        verbose_name_plural = '*תשובות משתמשים'
        unique_together = ('chapter', 'user', 'question_number')

