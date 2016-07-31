# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError

from .formula import (
    Argument,
    FormulaSet,
    formal_type,
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
        all_answers = [form.cleaned_data['formula'] for form in self.forms if 'formula' in form.cleaned_data]
        types = set(formal_type(a) for a in all_answers)

        if len(types) == 0:
            raise ValidationError('יש להזין לפחות תשובה אחת')
        if len(types) > 1:
            raise ValidationError('כל התשובות צריכות להיות מאותו סוג (נוסחה/טיעון)')
        if FormulaSet in types:
            raise ValidationError('לא ניתן להזין קבוצת נוסחאות - רק נוסחה בודדת או טיעון')
        if self.instance.followup == FormulationQuestion.DEDUCTION and types.pop() != Argument:
            raise ValidationError('כל תשובה חייבת להיות טיעון על מנת לשמש בשאלת המשך מסוג דדוקציה')
