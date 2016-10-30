# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import pre_delete, post_delete 
from django.dispatch import receiver
from django.utils import timezone

from .formula import (
    Formula,
    PredicateFormula,
    FormulaSet,
    PredicateFormulaSet,
    Argument,
    PredicateArgument,
    formal_type,
    formalize,
    get_argument,
)

import logging
logger = logging.getLogger(__name__)

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
    number = models.DecimalField(
        verbose_name='מספר',
        max_digits=3,
        decimal_places=1,
        unique=True,
        validators = [
            MaxValueValidator(100.),
            MinValueValidator(1.),
        ]
    )
    title = models.CharField(verbose_name='כותרת', max_length=40)
    gen_title = models.CharField(
        verbose_name='כותרת כללית (אופציונלי. שם זה ישמש לתצוגה במסך הראשי עבור פרקים מרובי חלקים)', max_length=40, null=True, blank=True
    )

    @property
    def chnum(self):
        return str(self.number)

    @property
    def chapter_display(self):
        return str(int(self.number))
    
    @property
    def part_display(self):
        return '%s%s' % (int(self.number), {
            '0': 'א',
            '1': 'ב',
            '2': 'ג',
            '3': 'ד',
            '4': 'ה',
            '5': 'ו',
            '6': 'ז',
            '7': 'ח',
            '8': 'ט',
            '9': 'י',
        }[str(self.number).split('.').pop()])
   
    @property
    def display(self):
        if self.has_parts():
            return self.part_display
        else:
            return self.chapter_display

    def parts(self):
        return Chapter.objects.filter(number__gte=int(self.number), number__lt=int(self.number)+1)

    def has_parts(self):
        return not self.is_first_part() or self.parts().count() > 1

    def is_first_part(self):
        return self.number == int(self.number)

    def num_questions(self, followups=False):
        if followups:
            questions = Question._filter(chapter=self)
            return len(questions) + sum(1 for q in questions if q.has_followup())
        else:
            return Question._count(chapter=self)
    num_questions.short_description = 'מספר שאלות'

    def questions(self):
        return Question._filter(chapter=self)

    def first_question(self):
        return min(self.questions(), key=lambda q: q.number)

    def is_open(self):
        return any(type(q) == OpenQuestion for q in self.questions())

    def user_answers(self):
        return UserAnswer.objects.filter(chapter=self)
   
    def reorder_questions(self, moved_num=None):
        """ renumbers questions if there are any gaps in numbers, starting 1 """
        questions = sorted(self.questions(), key=lambda q: q.number)
        next_num = 1
        for q in questions:
            if moved_num is None or moved_num != q.number:
                if q.number != next_num:
                    logger.debug('ch. %s: renumbering %s to %d', self.number, q, next_num)
                    q.number = next_num
                    q.save()
                next_num += 1

    def __unicode__(self):
        return '%s. %s' % (self.display, self.title)

    class Meta:
        verbose_name = 'פרק'
        verbose_name_plural = 'פרקים'
        ordering = ['number']

class Question(models.Model):

    CLEAN_CHECK_ANSWERS = True
    DEFAULT_NUM = 0

    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.CASCADE, null=True)
    number = models.PositiveIntegerField(default=DEFAULT_NUM, verbose_name='מספר', null=True)

    def _get_chapter(self):
        try:
            return self.chapter
        except Chapter.DoesNotExist:
            pass # chapter is deleted

    def user_answers(self, user=None):
        if self._get_chapter():
            kw = UserAnswer.get_kw(self)
            if user:
                kw['user'] = user
            return UserAnswer.objects.filter(chapter=self.chapter, **kw)
        return []
    
    def user_answer(self, user, is_followup=False):
        if is_followup and hasattr(self, 'original'):
            # original is set in FollowupQuestionView 
            kw = UserAnswer.get_kw(self.original)
        else:
            kw = UserAnswer.get_kw(self)
        return UserAnswer.objects.filter(user=user, chapter=self.chapter, is_followup=is_followup, **kw).first()

    def clean(self):
        super(Question, self).clean()
        if self.chapter_id:
            self._validate_affecting_answers()
            if self.number > self.DEFAULT_NUM:
                chapter_questions = Question._filter(chapter=self.chapter)
                other_nums = set([q.number for q in Question._filter(chapter=self.chapter) if not q.is_same(self)])
                chapter_changed, _ = self._chapter_changed()
                if self.number in other_nums and not chapter_changed:
                    raise ValidationError('כבר קיימת שאלה מספר %d בפרק %s' % (self.number, self.chapter.display))
            if self.chapter.is_open():
                if type(self) != OpenQuestion:
                    raise ValidationError('לא ניתן לשמור שאלה זו בפרק עם שאלות פתוחות')
            elif self.chapter.num_questions() > 0 and type(self) == OpenQuestion:
                    raise ValidationError('לא ניתן לשמור שאלה זו בפרק עם שאלות לא פתוחות')

    def _validate_affecting_answers(self):
        if self.CLEAN_CHECK_ANSWERS:
            chapter_has_answers = len(self.chapter.user_answers()) > 0
            if self._is_new():
                if chapter_has_answers:
                    # question is new and chapter already has answers
                    logger.error('%s has user answers, not adding new question %s', self.chapter, self)
                    raise ValidationError('לא ניתן להוסיף שאלה לפרק שיש לו תשובות משתמשים')
            elif chapter_has_answers:
                # question changed in a chapter with answers
                logger.error('%s has user answers, not editing question %s', self.chapter, self)
                raise ValidationError('לא ניתן לערוך שאלה בפרק שיש לו תשובות משתמשים')
            else:
                chapter_changed, existing_chapter = self._chapter_changed()
                if chapter_changed and existing_chapter.user_answers():
                    # question changed in a chapter with answers
                    logger.error('%s has user answers, not editing question %s', existing_chapter, self)
                    raise ValidationError('לא ניתן לערוך שאלה בפרק שיש לו תשובות משתמשים')
                
    def save(self, *args, **kwargs):
        logger.debug('saving %s', self)
        reorder_chapter = False
        if self.number == self.DEFAULT_NUM:
            # new question, set a number
            self._auto_number()
        else:
            chapter_changed, existing_chapter = self._chapter_changed()
            if chapter_changed:
                old_num = self.number
                # question moved to another chapter, renumber the question
                self._auto_number()
                reorder_chapter = True
        self.clean()
        super(Question, self).save(*args, **kwargs)
        if reorder_chapter:
            # reorder the chapter from which the question was moved (must be after save)
            existing_chapter.reorder_questions(moved_num=old_num)

    def _chapter_changed(self):
        existing_q = self._get_existing()
        existing_ch = existing_q.chapter if existing_q else None
        return existing_q and self.chapter != existing_ch, existing_ch

    def _get_existing(self):
        if not self._is_new():
            return type(self).objects.get(pk=self.pk)

    def _is_new(self):
        return self.pk is None

    def _auto_number(self):
        others = Question._filter(chapter=self.chapter)
        self.number = max(q.number for q in others) + 1 if others else 1
        logger.debug('setting number to %d', self.number)

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

    @property
    def _str(self):
        return '%s/%d' % (self.chapter.number, self.number)

    def is_same(self, other):
        return self.id == other.id and type(self) == type(other)
 
    def admin_display(self):
        return 'שאלה %s' % self.number
    admin_display.short_description = 'שאלה'

    class Meta:
        abstract = True
        ordering = ['number']

@receiver(post_delete)   
def delete_stuff(instance, sender, **kwargs):
    # do stuff upon question deletion
    if issubclass(sender, Question):
        self = instance
        logger.debug('post delete %s', self)
        # re-order other questions
        chapter = self._get_chapter()
        if chapter: # if chapter was not deleted
            chapter.reorder_questions()

class TextualQuestion(Question):
    text = models.TextField(verbose_name='טקסט')

    @property
    def short_text(self):
        return shorten_text(self.text)
 
    def admin_display(self):
        return '%s. %s' % (self.number, self.short_text)
    admin_display.short_description = 'שאלה'

    def admin_list_display(self):
        return '%s' % (shorten_text(self.text, size=130))

    def __unicode__(self):
        return '%s/%s. %s' % (self.chapter.number, self.number, self.short_text)

    class Meta(Question.Meta):
        abstract = True

class FormalQuestion(Question):

    def __unicode__(self):
        return '%s/%s. %s' % (self.chapter.number, self.number, self.formula)

    def admin_list_display(self):
        return '%s' % (self.formula)

    class Meta(Question.Meta):
        abstract = True

class FormulationQuestion(TextualQuestion):
    NONE = 'N'
    TRUTH_TABLE = 'T'
    DEDUCTION = 'D'
    MODEL = 'M'
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

    has_file = models.BooleanField(verbose_name='אפשר העלאת קובץ', default=False)

    class Meta(TextualQuestion.Meta):
        verbose_name = 'שאלת פתוחה'
        verbose_name_plural = 'שאלות פתוחות'

class ChoiceQuestion(TextualQuestion):

    class Meta(TextualQuestion.Meta):
        verbose_name = 'שאלת בחירה'
        verbose_name_plural = 'שאלות בחירה'

def validate_formula(formula, formula_cls=Formula):
    try:
        return formula_cls(formula).literal
    except:
        raise ValidationError({'formula':'הנוסחה שהוזנה אינה תקינה'})

def validate_formula_set(fset, formula_set_cls=FormulaSet):
    try:
        return formula_set_cls(fset).literal
    except:
        raise ValidationError({'formula':'הקבוצה שהוזנה אינה תקינה'})

def validate_argument(arg, argument_cls=Argument):
    try:
        return argument_cls(arg).literal
    except:
        msg = 'הטיעון שהוזן אינו תקין'
        raise ValidationError({'formula':msg})

def validate_deduction_argument(arg):
    try:
        a = get_argument(arg)
    except:
        raise ValidationError({'formula':'הטיעון שהוזן אינו תקין'})
    if a.formula_cls == Formula and not a.is_valid:
        raise ValidationError({'formula':'הטיעון שהוזן אינו ניתן להוכחה'})
    return a.literal

def validate_truth_table(x):
    pass

class SemanticsQuestion(FormalQuestion):
    FORMULA = 'F'
    SET = 'S'
    ARGUMENT = 'A'
    TABLE_CHOICES = (
        (FORMULA, 'נוסחה'),
        (SET,'קבוצה'),
        (ARGUMENT, 'טיעון'),
    )
    table_type = models.CharField(verbose_name='סוג',max_length=1,choices=TABLE_CHOICES, null=True)
    formula = models.CharField(verbose_name='נוסחה/טיעון/קבוצה', max_length=60, null=True)

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
        super(SemanticsQuestion, self).clean()
        self._set_table_type()
        if self.is_formula:
            self.formula = validate_formula(self.formula, self._formula_cls)
        elif self.is_set:
            self.formula = validate_formula_set(self.formula, self._formula_set_cls)
        elif self.is_argument:
            self.formula = validate_argument(self.formula, self._argument_cls)

    def save(self, *args, **kwargs):
        self._set_table_type()
        super(SemanticsQuestion, self).save(*args, **kwargs)

    def display(self):
        if self.is_formula:
            return self.formula
        if self.is_set:
            return self._formula_set_cls(self.formula).display
        if self.is_argument:
            return self._argument_cls(self.formula).display

    def _set_table_type(self):
        try:
            self.table_type = {
                self._formula_cls: self.FORMULA,
                self._formula_set_cls: self.SET,
                self._argument_cls: self.ARGUMENT
            }[formal_type(self.formula)]
        except:
            raise ValidationError({'formula':'קלט לא תקין'})

    class Meta(FormalQuestion.Meta):
        abstract = True
        unique_together = ('chapter', 'formula')

class TruthTableQuestion(SemanticsQuestion):

    _formula_cls = Formula
    _formula_set_cls = FormulaSet
    _argument_cls = Argument

    @property
    def options(self):
        if self.is_formula:
            return FORMULA_OPTIONS
        elif self.is_set:
            return SET_OPTIONS
        elif self.is_argument:
            return ARGUMENT_OPTIONS

    class Meta(SemanticsQuestion.Meta):
        verbose_name = 'שאלת טבלת אמת'
        verbose_name_plural = 'שאלות טבלת אמת'

class ModelQuestion(SemanticsQuestion):

    _formula_cls = PredicateFormula
    _formula_set_cls = PredicateFormulaSet
    _argument_cls = PredicateArgument

    class Meta(SemanticsQuestion.Meta):
        verbose_name = 'שאלת פשר'
        verbose_name_plural = 'שאלות פשר'

class DeductionQuestion(FormalQuestion):
    formula = models.CharField(verbose_name='טיעון', max_length=60)

    def clean(self):
        super(DeductionQuestion, self).clean()
        self.formula = validate_deduction_argument(self.formula)

    def display(self):
        return get_argument(self.formula).display

    class Meta(FormalQuestion.Meta):
        verbose_name = 'שאלת דדוקציה'
        verbose_name_plural = 'שאלות דדוקציה'
        unique_together = ('chapter', 'formula')

class FormulationAnswer(models.Model):
    formula = models.CharField(verbose_name='נוסחה/טיעון/קבוצה', max_length=60)
    question = models.ForeignKey(FormulationQuestion, verbose_name='שאלה', on_delete=models.CASCADE)

    def clean(self):
        super(FormulationAnswer, self).clean()
        try:
            formalize(self.formula)
        except:
            raise ValidationError('קלט לא תקין')
        
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
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.PROTECT)
    attempt = models.PositiveIntegerField(verbose_name='נסיונות')
    ongoing = models.BooleanField()
    time = models.DateTimeField(verbose_name='זמן הגשה', blank=True, null=True)

    def is_complete(self):
        """
        a submission is complete iff all chapter questions were answered including all followups
        this is premised on the assumption that a user can always advance to the followup question,
        even if the preliminary one is incorrect
        """
        user_answers = self.useranswer_set.all()
        chapter_questions = {q.number: q for q in self.chapter.questions()}
        chapter_followups = {q.number for q in chapter_questions.itervalues() if q.has_followup()}
        answered_questions = {a.question_number: a.correct for a in user_answers if not a.is_followup}
        answered_followups = {a.question_number for a in user_answers if a.is_followup}
        return set(chapter_questions.keys()) == set(answered_questions.keys()) and chapter_followups == answered_followups

    def is_ready(self):
        if self.chapter.is_open():
            answers = OpenAnswer.objects.filter(user_answer__user=self.user, question__chapter=self.chapter)
            if not all(a.checked for a in answers):
                return False
        return self.is_complete()

    @classmethod
    def MAX_ATTEMPTS(cls):
        return GlobalSettings.get().max_attempts

    @property
    def max_attempts(self):
        return self.MAX_ATTEMPTS() if not self.chapter.is_open() else 1
 
    def can_try_again(self):
        return self.attempt < self.max_attempts

    @property
    def remaining(self):
        return self.max_attempts - self.attempt

    @property
    def user_id_num(self):
        return self.user.userprofile.id_num if hasattr(self.user, 'userprofile') else ''

    @property
    def user_group(self):
        return self.user.userprofile.group if hasattr(self.user, 'userprofile') else ''

    @property
    def percent_correct_f(self):
        return self.percent_correct()

    def percent_correct(self):
        _, _, pct = self.correctness_data()
        return pct
    percent_correct.short_description = 'ציון'

    @property
    def localtime_str(self):
        if self.time:
            return timezone.localtime(self.time).strftime('%d/%m/%Y %H:%M')

    def correctness_data(self):
        """
        returns dict of (question number, is followup) -> grade/correct
        """
        if self.chapter.is_open() and self.is_ready():
            answers = OpenAnswer.objects.filter(user_answer__user=self.user, question__chapter=self.chapter)
            answer_data = {
                (ans.question.number, False): float(ans.grade)
                for ans in answers
            }
            num_correct = sum(answer_data.itervalues())
        else:
            answer_data = {
                (ans.question_number, ans.is_followup): ans.correct 
                for ans in self.useranswer_set.all()
            }
            num_correct = sum(1 for correct in answer_data.itervalues() if correct)

        pct = int(round(num_correct * 100. / self.chapter.num_questions(followups=True)))
        return answer_data, num_correct, pct

    @property
    def chapter_number_f(self):
        return self.chapter.number

    def chapter_number(self):
        return self.chapter.number
    chapter_number.short_description = 'פרק'

    def __unicode__(self):
        return '%s/%s%s complete=%s, ongoing=%s, attempts=%d, can-retry=%s, pct=%.1f' % (
            self.user,
            self.chapter.number,
            ' [%s]' % self.time if self.time else '',
            self.is_complete(),
            self.ongoing,
            self.attempt,
            self.can_try_again(),
            self.percent_correct(),
        )

    class Meta:
        verbose_name = 'הגשה'
        verbose_name_plural = 'הגשות'
        unique_together = ('chapter', 'user')
        ordering = ['chapter']

class UserAnswer(models.Model):
    user = models.ForeignKey(User, verbose_name='משתמש', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, verbose_name='פרק', on_delete=models.PROTECT)
    submission = models.ForeignKey(ChapterSubmission, verbose_name='הגשת פרק', on_delete=models.CASCADE)

    _cq = models.ForeignKey(ChoiceQuestion, on_delete=models.PROTECT, null=True)
    _oq = models.ForeignKey(OpenQuestion, on_delete=models.PROTECT, null=True)
    _fq = models.ForeignKey(FormulationQuestion, on_delete=models.PROTECT, null=True)
    _tq = models.ForeignKey(TruthTableQuestion, on_delete=models.PROTECT, null=True)
    _mq = models.ForeignKey(ModelQuestion, on_delete=models.PROTECT, null=True)
    _dq = models.ForeignKey(DeductionQuestion, on_delete=models.PROTECT, null=True)

    correct = models.BooleanField(verbose_name='תשובה נכונה')
    answer = models.TextField()
    is_followup = models.BooleanField(default=False)
    time = models.DateTimeField(verbose_name='זמן', blank=True, null=True)

    def set_question(self, q):
        if type(q) == ChoiceQuestion:
            self._cq = q
        elif type(q) == OpenQuestion:
            self._oq = q
        elif type(q) == FormulationQuestion:
            self._fq = q
        elif type(q) == TruthTableQuestion:
            self._tq = q
        elif type(q) == ModelQuestion:
            self._mq = q
        elif type(q) == DeductionQuestion:
            self._dq = q
        else:
            raise ValueError('Unknown question type: %s' % type(q))

    @classmethod
    def get_kw(cls, q):
        if type(q) == ChoiceQuestion:
            kw = {'_cq': q}
        elif type(q) == OpenQuestion:
            kw = {'_oq': q}
        elif type(q) == FormulationQuestion:
            kw = {'_fq': q}
        elif type(q) == TruthTableQuestion:
            kw = {'_tq': q}
        elif type(q) == ModelQuestion:
            kw = {'_mq': q}
        elif type(q) == DeductionQuestion:
            kw = {'_dq': q}
        else:
            raise ValueError('Unknown question type: %s' % type(q))
        return kw

    @property
    def question(self):
        for q in self._all_q:
            if q:
                return q

    @property
    def question_number(self):
        q = self.question
        if q:
            return q.number

    @property
    def _all_q(self):
        return [self._cq, self._oq, self._fq, self._tq, self._mq, self._dq]

    def is_submitted(self):
        """ returns true iff chapter was submitted with this answer """
        return self.submission and self.submission.time and (self.time < self.submission.time)

    def save(self, *args, **kwargs):
        if not self.question:
            logger.error('%s has no question, aborting save', self)
            raise ValidateionError('cannot save user answer with no question')
        super(UserAnswer, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s/%s/%s/%s' % (self.user, self.chapter.number, self.question_number, 'T' if self.correct else 'F')

    class Meta:
        verbose_name = 'תשובת משתמש'
        verbose_name_plural = '[תשובות משתמשים]'
        unique_together = ('chapter', 'user', '_cq', '_oq', '_fq', '_tq', '_mq', '_dq', 'is_followup')

def name_file(instance, filename):
    chapnum = str(instance.question.chapter.number).replace('.','-')
    path = 'uploads/%s/ch%s' % (timezone.localtime(timezone.now()).year, chapnum)
    extension = filename.rsplit('.', 1).pop()
    name = '%s_%s_%s.%s' % (instance.user_answer.user.username, chapnum, instance.question.number, extension)
    return os.path.join(path, name)

class OpenAnswer(models.Model):

    text = models.TextField(verbose_name='טקסט')
    question = models.ForeignKey(OpenQuestion, verbose_name='שאלה', on_delete=models.PROTECT)
    upload = models.FileField(verbose_name='קובץ', upload_to=name_file, null=True, blank=True)
    user_answer = models.OneToOneField(UserAnswer, on_delete=models.CASCADE, unique=True)
    grade = models.DecimalField(
        verbose_name='ניקוד (בין 0 ל-1)',
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=False,
        validators = [
            MaxValueValidator(1.),
            MinValueValidator(0.),
        ]
    )
    comment = models.TextField(verbose_name='הערות (אופציונלי)', null=True, blank=True, max_length=500)

    @property
    def checked(self):
        return self.grade is not None

    def save(self, *args, **kwargs):
        try:
            # delete old file if replaced
            this = OpenAnswer.objects.get(id=self.id)
            if this.upload != self.upload:
                logger.debug('%s upload updated, deleting previous file', self)
                this.upload.delete(save=False)
        except: pass # new file
        super(OpenAnswer, self).save(*args, **kwargs)

    @property
    def short_text(self):
        return shorten_text(self.text)
 
    def __unicode__(self):
        return '%s file=%s text=%s' % (self.user_answer, self.upload, self.short_text)

    class Meta:
        verbose_name = 'תשובה פתוחה'
        verbose_name_plural = 'תשובות פתוחות'

# handle open answer deletion
@receiver(post_delete)   
def delete_open_answer(instance, sender, **kwargs):
    if issubclass(sender, OpenAnswer):
        # delete file
        logger.debug('post delete %s', instance)
        instance.upload.delete(save=False)

########################################################################################################
# Other models

# see: https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#extending-the-existing-user-model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.CharField(max_length=2, verbose_name='מספר קבוצה')
    id_num = models.CharField(
        max_length=9,
        verbose_name='מספר ת.ז',
        validators=[RegexValidator(
            regex='^\d{9}$',
            message='מספר ת.ז צריך להיות באורך 9 ספרות',
        )]
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return '%s/%s/%s' % (self.user, self.group, self.id_num)
    __repr__ = __str__
    __unicode__ = __str__

    class Meta:
        verbose_name = 'פרופיל'
        verbose_name_plural = 'פרופילים'

class Stat(models.Model):
    user_answer = models.ForeignKey(UserAnswer, on_delete=models.CASCADE)
    correct = models.BooleanField()

# TODO: use this in places
class GlobalSettings(models.Model):
    course_id = models.CharField(
        verbose_name='מספר קורס',
        max_length=30,
        default='0618101201',
        validators=[RegexValidator(
            regex='^\d+$',
            message='יש להזין ספרות בלבד',
        )]
    )
    max_group_id = models.CharField(
        verbose_name='מספר קבוצה מקסימלי',
        max_length=2,
        default='09',
        validators=[RegexValidator(
            regex='^\d{2}$',
            message='יש להזין שתי ספרות',
        )]
    )
    max_attempts = models.PositiveIntegerField(
        verbose_name='מספר נסיונות מקסימלי להגשה',
        default=3,
        validators = [
            MaxValueValidator(100),
            MinValueValidator(1),
        ]
    )
    max_file_size = models.PositiveIntegerField( # in MB
        verbose_name='גודל מקסימלי להעלאת קובץ (MB)',
        default=3,
        validators = [
            MaxValueValidator(50),
            MinValueValidator(1),
        ]
    )
    ldap_enabled = models.BooleanField(verbose_name='אימות משתמשי אוניברסיטה', default=True)

    @classmethod
    def get(cls):
        all_settings = cls.objects.all()
        assert all_settings.count() == 1, ('got %d global settings objects!' % all_settings.count())
        return all_settings[0]
 
    def save(self, *args, **kwargs):
        logger.info('saving settings: %s', self.__dict__)
        super(GlobalSettings, self).save(*args, **kwargs)

    def __str__(self):
        return 'app-settings'
    __repr__ = __str__
    __unicode__ = __str__

    class Meta:
        verbose_name = 'הגדרות כלליות'
        verbose_name_plural = 'הגדרות כלליות'

