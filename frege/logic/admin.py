# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput

from .actions import export_as_csv_action
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
    extra = 0
    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

class OpenQuestionInline(admin.StackedInline):
    model = OpenQuestion
    extra = 0

class FormulationQuestionInline(admin.StackedInline):
    model = FormulationQuestion
    extra = 0

class ChoiceQuestionInline(admin.StackedInline):
    model = ChoiceQuestion
    extra = 0

class FormalQuestionInline(admin.StackedInline):
    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class TruthTableQuestionInline(FormalQuestionInline):
    model = TruthTableQuestion
    extra = 0

class DeductionQuestionInline(FormalQuestionInline):
    model = DeductionQuestion
    extra = 0

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'chapter']
    list_filter = ['chapter']
    ordering = ['chapter', 'number']

class TextualQuestionAdmin(QuestionAdmin):
    search_fields = ['text']

class OpenQuestionAdmin(TextualQuestionAdmin):
    pass

class FormulationQuestionAdmin(TextualQuestionAdmin):
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

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'question_number', 'correct']
    ordering = ['user', 'chapter', 'question_number']
    readonly_fields = ['user', 'chapter', 'question_number', 'correct']
    actions = [export_as_csv_action(fields=['user', 'question_number', 'correct'])]
 
    def has_add_permission(self, request, obj=None):
        return False

class ChapterSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'percent_correct', 'attempt']
    list_filter = ['user', 'chapter']
    ordering = ['chapter', 'user']
    readonly_fields = ['user', 'chapter']
    actions = [export_as_csv_action(fields={
        'user': 'user',
        'chapter': 'chapter_number_f',
        'percent': 'percent_correct_f',
    })]
 
    def has_add_permission(self, request, obj=None):
        return False

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
