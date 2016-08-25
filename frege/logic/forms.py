# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError

from .formula import (
    Formula,
    PredicateFormula,
    Argument,
    FormulaSet,
    formal_type,
    formalize,
)
from .models import (
    Question,
    FormulationQuestion,
    TruthTableQuestion,
)

class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        exclude = ['number']

class TruthTableQuestionForm(QuestionForm):

    class Meta(QuestionForm.Meta):
        model = TruthTableQuestion
        exclude = QuestionForm.Meta.exclude + ['table_type']

class FormulationAnswerFormSet(forms.BaseInlineFormSet):

    def clean(self):
        super(FormulationAnswerFormSet, self).clean()

        if any(form._errors for form in self.forms):
            return

        all_answers = [form.cleaned_data['formula'] for form in self.forms if 'formula' in form.cleaned_data]
        types = set(formal_type(a) for a in all_answers)

        if len(types) == 0:
            raise ValidationError('יש להזין לפחות תשובה אחת')
        if len(types) > 1:
            raise ValidationError('כל התשובות צריכות להיות מאותו סוג (נוסחה/טיעון)')
        if FormulaSet in types:
            raise ValidationError('לא ניתן להזין קבוצת נוסחאות - רק נוסחה בודדת או טיעון')
        if Argument in types:
            arguments = [formalize(a) for a in all_answers]
            if len(set(a.formula_cls for a in arguments)) > 1:
                raise ValidationError('לא ניתן להזין טיעונים מתחשיבים שונים')
        else:
            arguments = []

        followup = self.instance.followup
        if followup == FormulationQuestion.DEDUCTION:
            if types.pop() != Argument:
                raise ValidationError('עבור שאלת המשך מסוג דדוקציה התשובות חייבות להיות טיעונים')
            for argument in arguments:
                if argument.formula_cls == Formula and not argument.is_valid:
                   raise ValidationError(u'הטיעון %s אינו ניתן להוכחה' % answer)
        elif followup == FormulationQuestion.TRUTH_TABLE:
            answer_type = types.pop()
            if answer_type == PredicateFormula or any(a.formula_cls == PredicateFormula for a in arguments):
                raise ValidationError('עבור שאלת המשך מסוג טבלת אמת התשובות חייבות להיות בשפת תחשיב הפסוקים')
        elif followup == FormulationQuestion.MODEL:
            answer_type = types.pop()
            if answer_type == Formula or any(a.formula_cls == Formula for a in arguments):
                raise ValidationError('עבור שאלת המשך מסוג פשר התשובות חייבות להיות בשפת תחשיב הפרדיקטים')

