from django.contrib import admin

from .models import (
    Chapter,
    OpenQuestion,
    FormulationQuestion,
    ChoiceQuestion,
    TruthTableQuestion,
    DeductionQuestion,
    FormulationAnswer,
    Choice,
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
admin.site.register(TruthTableQuestion)
admin.site.register(DeductionQuestion)
