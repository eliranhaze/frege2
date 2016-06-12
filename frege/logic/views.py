from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .models import (
    Chapter,
    ChoiceQuestion,
)

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        return Chapter.objects.all()

class ChapterView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'

    def get_object(self):
        return get_object_or_404(Chapter, number=self.kwargs['number'])

    def get_context_data(self, **kwargs):
        context = super(ChapterView, self).get_context_data(**kwargs)
        context['question_list'] = ChoiceQuestion.objects.filter(chapter__number=self.kwargs['number'])
        return context

