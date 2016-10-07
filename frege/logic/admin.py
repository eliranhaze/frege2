# -*- coding: utf-8 -*-
from collections import OrderedDict
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.forms.widgets import TextInput
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.html import format_html

from .actions import export_as_csv_action
from .forms import (
    QuestionForm,
    ChoiceFormSet,
    FormulationAnswerFormSet,
    TruthTableQuestionForm,
    OpenAnswerForm,
)
from .models import (
    Chapter,
    OpenQuestion,
    FormulationQuestion,
    FormulationAnswer,
    ChoiceQuestion,
    Choice,
    TruthTableQuestion,
    ModelQuestion,
    DeductionQuestion,
    UserAnswer,
    ChapterSubmission,
    OpenAnswer,
    UserProfile,
    GlobalSettings,
)
import logging
logger = logging.getLogger(__name__)

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
    formset = ChoiceFormSet
    extra = 0

#class QuestionInline(admin.StackedInline):
#    extra = 0
#
#    def get_formset(self, *args, **kwargs):
#        self.exclude = ['number']
#        return super(QuestionInline, self).get_formset(*args, **kwargs)
#
#class OpenQuestionInline(QuestionInline):
#    model = OpenQuestion
#
#class FormulationQuestionInline(QuestionInline):
#    model = FormulationQuestion
#
#class ChoiceQuestionInline(QuestionInline):
#    model = ChoiceQuestion
#
#class FormalQuestionInline(QuestionInline):
#    formfield_overrides = {
#        models.CharField: formal_text_widget
#    }
#
#class TruthTableQuestionInline(FormalQuestionInline):
#    model = TruthTableQuestion
#
#class ModelQuestionInline(FormalQuestionInline):
#    model = ModelQuestion
#
#class DeductionQuestionInline(FormalQuestionInline):
#    model = DeductionQuestion
#
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['admin_display', 'chapter']
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
    list_display = ['admin_display', 'chapter', 'formula']
    search_fields = ['formula']

    formfield_overrides = {
        models.CharField: formal_text_widget
    }

class TruthTableQuestionAdmin(FormalQuestionAdmin):
    list_display = ['number', 'chapter', 'table_type', 'formula']
    list_filter = QuestionAdmin.list_filter + ['table_type']
    form = TruthTableQuestionForm

class ModelQuestionAdmin(TruthTableQuestionAdmin):
    pass

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'question_number', 'correct', 'is_followup', 'time']
    ordering = ['user', 'chapter', 'question_number']
    readonly_fields = ['user', 'chapter', 'question_number', 'correct', 'is_followup', 'time', 'answer', 'submission']
    actions = [export_as_csv_action(fields=['user', 'question_number', 'correct'])]
 
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

class GroupFilter(admin.SimpleListFilter):
    title = 'קבוצה'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        groups = list(set(cs.user.userprofile.group for cs in ChapterSubmission.objects.all() if hasattr(cs.user, 'userprofile')))
        return (
            (g, g) for g in groups
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**self._get_kw())
        else:
            return queryset.all()

    def _get_kw(self):
        return {'user__userprofile__group': self.value()}

class AnswerGroupFilter(GroupFilter):
    def _get_kw(self):
        return {'user_answer__user__userprofile__group': self.value()}

class OpenAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'question', 'grade']
    list_filter = [AnswerGroupFilter, 'grade', 'question__chapter', 'question__number', 'user_answer__user']
    ordering = ['user_answer__user', 'question__number']
    readonly_fields = ['user', 'answer_text', 'upload', 'chapter', 'question_text']
    form = OpenAnswerForm
 
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def user(self, obj):
        return obj.user_answer.user
    user.short_description = 'משתמש'

    def chapter(self, obj):
        return obj.question.chapter
    chapter.short_description = 'פרק'

    def answer_text(self, obj):
        return '\n\n%s' % (obj.text)
    answer_text.short_description = 'תשובה'

    def question_text(self, obj):
        return '\n\n(%d) %s' % (obj.question.number, obj.question.text)
    question_text.short_description = 'שאלה'

class ChapterSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'percent_correct', 'time', 'attempt']
    list_filter = [GroupFilter, 'chapter', 'time', 'user']
    ordering = ['chapter', 'user']
    readonly_fields = ['user', 'chapter', 'time', 'attempt']
    exclude = ['ongoing']
    actions = [export_as_csv_action(fields=OrderedDict([
        ('user', 'user'),
        ('id', 'user_id_num'),
        ('group', 'user_group'),
        ('chapter', 'chapter_number_f'),
        ('percent', 'percent_correct_f'),
        ('time', 'localtime_str'),
    ]))]
 
    def has_add_permission(self, request, obj=None):
        return False

#    def get_queryset(self, *args, **kwargs):
#        # return only ready submissions
#        submission_ids = [s.id for s in ChapterSubmission.objects.all() if s.is_ready()]
#        return ChapterSubmission.objects.filter(id__in=submission_ids)

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'num_questions', 'show_url']
    search_fields = ['title']

    def show_url(self, chapter):
        return format_html("<a href='chq/%s'>רשימת שאלות פרק %s</a>" % (chapter.number, chapter.display.encode('utf-8')))
    show_url.short_description = 'שאלות'

    def get_urls(self):
        urls = super(ChapterAdmin, self).get_urls()
        return [
            url(r'^chq/(?P<chnum>[0-9]+\.[0-9]+)/$', self.questions_view, name='chapter-questions'),
        ] + urls

    def questions_view(self, request, chnum):

        context = {}
        chapter = get_object_or_404(Chapter, number=chnum) 
        questions = chapter.questions()

        if request.method == 'POST':
            logger.info('%s: post chapter %s questions view', request.user, chnum) 
            qdata = request.POST.get('qdata')
            magic_number = 9999999
            if qdata:
                try:
                    with transaction.atomic():
                        questions_by_num = {q.number: q for q in questions}
                        changed = []
                        for item in qdata.split(','):
                            if ':' in item:
                                qnum, new_num = item.split(':')
                                qnum = int(qnum.replace('q',''))
                                new_num = int(new_num)
                                if new_num != qnum:
                                    question = questions_by_num[qnum]
                                    logger.debug('%s: chapter %s questions: setting %d->%d', request.user, chnum, qnum, new_num)
                                    question.number = new_num + magic_number
                                    question.save()
                                    changed.append(question)
                        for question in changed:
                            question.number -= magic_number
                            logger.debug('%s: chapter %s questions: saving %s', request.user, chnum, question)
                            question.save()
                except ValidationError, e:
                    # get the questions anew
                    questions = chapter.questions()
                    context['error'] = e.message

        questions = [
            (q, reverse('admin:logic_%s_change' % str(type(q).__name__).lower(), args=(q.id,)))
            for q in sorted(questions, key=lambda q: q.number)
        ]

        context.update(dict(
            self.admin_site.each_context(request),
            questions=questions,
            chapter=chapter,
        ))
        return TemplateResponse(request, 'admin/chapter_questions.html', context)

#    inlines = [
#        OpenQuestionInline,
#        FormulationQuestionInline,
#        ChoiceQuestionInline,
#        TruthTableQuestionInline,
#        ModelQuestionInline,
#        DeductionQuestionInline,
#    ]

#########################################################3
# User profile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'פרופיל משתמש'

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = BaseUserAdmin.list_display + ('group',)
    list_filter = BaseUserAdmin.list_filter + ('userprofile__group',)

    def group(self, obj):
        return obj.userprofile.group
    group.short_description = 'מספר קבוצה'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
#########################################################3

class GlobalSettingsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

admin.site.register(Chapter, ChapterAdmin)
admin.site.register(OpenQuestion, OpenQuestionAdmin)
admin.site.register(FormulationQuestion, FormulationQuestionAdmin)
admin.site.register(ChoiceQuestion, ChoiceQuestionAdmin)
admin.site.register(TruthTableQuestion, TruthTableQuestionAdmin)
#admin.site.register(ModelQuestion, ModelQuestionAdmin)
admin.site.register(DeductionQuestion, FormalQuestionAdmin)
admin.site.register(ChapterSubmission, ChapterSubmissionAdmin)
#admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(OpenAnswer, OpenAnswerAdmin)
admin.site.register(GlobalSettings, GlobalSettingsAdmin)

# override admin stuff like so
admin.site.site_title = 'ממשק ניהול'
admin.site.site_header = 'ממשק ניהול'
