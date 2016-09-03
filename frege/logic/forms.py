# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError

from .formula import (
    Formula,
    PredicateFormula,
    Argument,
    PredicateArgument,
    FormulaSet,
    formal_type,
)
from .models import (
    Question,
    FormulationQuestion,
    TruthTableQuestion,
    OpenAnswer,
)

class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        exclude = ['number']

class TruthTableQuestionForm(QuestionForm):

    class Meta(QuestionForm.Meta):
        model = TruthTableQuestion
        exclude = QuestionForm.Meta.exclude + ['table_type']

class OpenAnswerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
       super(OpenAnswerForm, self).__init__(*args, **kwargs)

    class Meta:
        model = OpenAnswer
        exclude = ['user_answer', 'question', 'text']

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
            raise ValidationError('כל התשובות צריכות להיות מאותו סוג')
        if FormulaSet in types:
            raise ValidationError('לא ניתן להזין קבוצת נוסחאות - רק נוסחה בודדת או טיעון')

        followup = self.instance.followup
        if followup == FormulationQuestion.DEDUCTION:
            answer_type = types.pop()
            if not issubclass(answer_type, Argument):
                raise ValidationError('עבור שאלת המשך מסוג דדוקציה התשובות חייבות להיות טיעונים')
            if answer_type == Argument:
                for answer in all_answers:
                    if not Argument(answer).is_valid:
                       raise ValidationError(u'הטיעון %s אינו ניתן להוכחה' % answer)
        elif followup == FormulationQuestion.TRUTH_TABLE:
            if types.pop() in (PredicateFormula, PredicateArgument):
                raise ValidationError('עבור שאלת המשך מסוג טבלת אמת התשובות חייבות להיות בשפת תחשיב הפסוקים')
        elif followup == FormulationQuestion.MODEL:
            if types.pop() in (Formula, Argument):
                raise ValidationError('עבור שאלת המשך מסוג פשר התשובות חייבות להיות בשפת תחשיב הפרדיקטים')

