# -*- coding: utf-8 -*-
from django.contrib import admin

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
    UserChapter,
)

class FormulationAnswerInline(admin.StackedInline):
    model = FormulationAnswer
    extra = 0

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

class TruthTableQuestionInline(admin.StackedInline):
    model = TruthTableQuestion
    extra = 0

class DeductionQuestionInline(admin.StackedInline):
    model = DeductionQuestion
    extra = 0

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'chapter']
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

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'question_number', 'correct']
    ordering = ['user', 'chapter', 'question_number']
    readonly_fields = ['user', 'chapter', 'question_number', 'correct']
    actions = [export_as_csv_action(fields=['user', 'question_number', 'correct'])]
 
    def has_add_permission(self, request, obj=None):
        return False

class UserChapterAdmin(admin.ModelAdmin):
    #TODO: link this model with UserAnswer so for delete cascade?
    list_display = ['user', 'chapter_number', 'percent_correct']
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
admin.site.register(TruthTableQuestion, QuestionAdmin)
admin.site.register(DeductionQuestion, QuestionAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(UserChapter, UserChapterAdmin)
