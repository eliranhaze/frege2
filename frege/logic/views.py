from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
)

def get_question_or_404(**kwargs):
    result = Question._filter(**kwargs)
    if not result:
        raise Http404('Question does not exist: %s' % kwargs)
    assert len(result) == 1
    return result[0]
 
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        return Chapter.objects.all()

class ChapterView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'

    def get_object(self):
        print 'VIEW:', self.__class__.__name__
        return get_object_or_404(Chapter, number=self.kwargs['chnum'])

    def get_context_data(self, **kwargs):
        context = super(ChapterView, self).get_context_data(**kwargs)
        questions = Question._filter(chapter__number=self.kwargs['chnum'])
        context['question_list'] = Question._filter(chapter__number=self.kwargs['chnum'])
        if len(questions) == 0:
            self.template_name = 'logic/index.html'
        else:
            first_question = questions[0] # TODO: determine the first question for this user
            context['question'] = first_question
            if type(first_question) == ChoiceQuestion:
                self.template_name = 'logic/choice.html'

        print 'TEMPLATE', self.template_name
        return context

    def post(self, request, *args, **kwargs):
        print 'Got', request.POST
        return render(request, self.template_name) 

class QuestionView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'
    context_object_name = 'question'

    def get_object(self):
        print 'VIEW:', self.__class__.__name__
        return get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        context['chapter'] = self.object.chapter
        if type(self.object) == ChoiceQuestion:
            self.template_name = 'logic/choice.html'
        return context

    def post(self, request, *args, **kwargs):
        print 'Got', request.POST
        return render(request, self.template_name)


