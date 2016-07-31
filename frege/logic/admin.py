# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput

from .actions import export_as_csv_action
from .forms import (
    QuestionForm,
    FormulationAnswerFormSet,
    TruthTableQuestionForm,
)
from .models import (
    Chapter,
    OpenQuestion,
    FormulationQuestion,
    FormulationAnswer,
    ChoiceQuestion,
    Choice,
    TruthTableQuestion,
    DeductionQuestion,
    UserAnswer,
    ChapterSubmission,
)

formal_text_widget = {'widget': TextInput(attrs={
    'dir' : 'ltr',
    'size' :'60',
    'autocomplete' : 'off',
})}
    
class FormulationAnswerInline(admin.StackedInline):
    model = FormulationAnswer
    formset = FormulationAnswerFormSet
    extra = 0
    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

class QuestionInline(admin.StackedInline):
    extra = 0

    def get_formset(self, *args, **kwargs):
        self.exclude = ['number']
        return super(QuestionInline, self).get_formset(*args, **kwargs)

class OpenQuestionInline(QuestionInline):
    model = OpenQuestion

class FormulationQuestionInline(QuestionInline):
    model = FormulationQuestion

class ChoiceQuestionInline(QuestionInline):
    model = ChoiceQuestion

class FormalQuestionInline(QuestionInline):
    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class TruthTableQuestionInline(FormalQuestionInline):
    model = TruthTableQuestion

class DeductionQuestionInline(FormalQuestionInline):
    model = DeductionQuestion

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'chapter']
    list_filter = ['chapter']
    ordering = ['chapter', 'number']
    form = QuestionForm

class TextualQuestionAdmin(QuestionAdmin):
    search_fields = ['text']

class OpenQuestionAdmin(TextualQuestionAdmin):
    pass

class FormulationQuestionAdmin(TextualQuestionAdmin):
    list_display = TextualQuestionAdmin.list_display + ['followup']
    list_filter = TextualQuestionAdmin.list_filter + ['followup']

    inlines = [
        FormulationAnswerInline,
    ]

class ChoiceQuestionAdmin(TextualQuestionAdmin):
    inlines = [
        ChoiceInline,
    ]

class FormalQuestionAdmin(QuestionAdmin):
    list_display = ['number', 'chapter', 'formula']
    search_fields = ['formula']

    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class TruthTableQuestionAdmin(FormalQuestionAdmin):
    list_display = ['number', 'chapter', 'table_type', 'formula']
    list_filter = QuestionAdmin.list_filter + ['table_type']
    form = TruthTableQuestionForm

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'question_number', 'correct']
    ordering = ['user', 'chapter', 'question_number']
    readonly_fields = ['user', 'chapter', 'question_number', 'correct']
    actions = [export_as_csv_action(fields=['user', 'question_number', 'correct'])]
 
    def has_add_permission(self, request, obj=None):
        return False

class ChapterSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'percent_correct', 'time', 'attempt']
    list_filter = ['user', 'chapter', 'time']
    ordering = ['chapter', 'user']
    readonly_fields = ['user', 'chapter', 'ongoing', 'time', 'attempt']
    actions = [export_as_csv_action(fields={
        'user': 'user',
        'chapter': 'chapter_number_f',
        'percent': 'percent_correct_f',
    })]
 
    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, *args, **kwargs):
        # return only submitted submissions
        return ChapterSubmission.objects.filter(time__isnull=False)

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'num_questions']
    search_fields = ['title']
    inlines = [
        OpenQuestionInline,
        FormulationQuestionInline,
        ChoiceQuestionInline,
        TruthTableQuestionInline,
        DeductionQuestionInline,
    ]

admin.site.register(Chapter, ChapterAdmin)
admin.site.register(OpenQuestion, OpenQuestionAdmin)
admin.site.register(FormulationQuestion, FormulationQuestionAdmin)
admin.site.register(ChoiceQuestion, ChoiceQuestionAdmin)
admin.site.register(TruthTableQuestion, TruthTableQuestionAdmin)
admin.site.register(DeductionQuestion, FormalQuestionAdmin)
admin.site.register(ChapterSubmission, ChapterSubmissionAdmin)

# override admin stuff like so
admin.site.site_title = 'ממשק ניהול'
admin.site.site_header = 'ממשק ניהול'
