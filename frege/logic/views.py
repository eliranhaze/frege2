from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
)

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        return Chapter.objects.all()

class ChapterView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'

    def get_object(self):
        u = self.request.user
        print 'USER: %s, %s' % (u.id, type(u))
        return get_object_or_404(Chapter, number=self.kwargs['number'])

    def get_context_data(self, **kwargs):
        context = super(ChapterView, self).get_context_data(**kwargs)
        questions = Question._filter(chapter__number=self.kwargs['number'])
        context['question_list'] = Question._filter(chapter__number=self.kwargs['number'])
        if len(questions) == 0:
            self.template_name = 'logic/index.html'
        else:
            first_question = questions[0] # TODO: determine the first question for this user
            context['question'] = first_question
            if type(first_question) == ChoiceQuestion:
                self.template_name = 'logic/choice.html'

        print 'TEMPLATE', self.template_name
        return context

