from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
    Choice,
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

    def dispatch(self, request, chnum):
        chapter = Chapter.objects.get(number=chnum)
        questions = Question._filter(chapter__number=chapter.number)
        question = questions[0] # TODO: determine the first question for this user
        return HttpResponseRedirect(reverse('logic:question', args=(chapter.number,question.number)))

class QuestionView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'
    context_object_name = 'question'

    def get_object(self):
        return get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        context['chapter'] = self.object.chapter
        if type(self.object) == ChoiceQuestion:
            self.template_name = 'logic/choice.html'
        return context

    def post(self, request, *args, **kwargs):
        choice = Choice.objects.get(id=request.POST['choice'])
        return JsonResponse({'correct':choice.is_correct})


