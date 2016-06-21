from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .formula import Formula, TruthTable
from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
    Choice,
    TruthTableQuestion,
    UserAnswer,
    UserChapter,
)

def get_question_or_404(**kwargs):
    question = Question._get(**kwargs)
    if not question:
        raise Http404('Question does not exist: %s' % kwargs)
    return question

def next_question(chapter, user):
    questions = Question._filter(chapter__number=chapter.number)
    for question in questions:
        if not question.user_answer(user):
            return question

def next_question_url(chapter, user):
    question = next_question(chapter, user)
    if question:
        url = reverse('logic:question', args=(chapter.number,question.number))
    else:
        url = reverse('logic:chapter-summary', args=(chapter.number,))
    return url

def chapter_questions_user_data(chapter, user):
    user_answers = {ans.question_number : ans.correct \
                    for ans in UserAnswer.objects.filter(user=user, chapter=chapter)}
    return {q.number : user_answers.get(q.number) for q in chapter.questions()}

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        return Chapter.objects.all()

class AboutView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/about.html'
    def get_object(self):
        return None

class ChapterView(LoginRequiredMixin, generic.DetailView):

    def get_object(self):
        return get_object_or_404(Chapter, number=self.kwargs['chnum'])

    def dispatch(self, request, chnum):
        chapter = get_object_or_404(Chapter, number=chnum)
        return HttpResponseRedirect(next_question_url(chapter, request.user))

class ChapterSummaryView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter_summary.html'

    def get_object(self):
        return get_object_or_404(Chapter, number=self.kwargs['chnum'])

    def get_context_data(self, **kwargs):
        context = super(ChapterSummaryView, self).get_context_data(**kwargs)
        chap_questions = chapter_questions_user_data(self.object, self.request.user)
        context['chap_questions'] = chap_questions
        context['num_correct'] = sum(1 for _, correct in chap_questions.iteritems() if correct)
        return context

class QuestionView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'
    context_object_name = 'question'

    def get_object(self):
        return get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        question = self.object
        context['chapter'] = question.chapter
        context['chap_questions'] = chapter_questions_user_data(question.chapter, self.request.user)
        if type(question) == ChoiceQuestion:
            self.template_name = 'logic/choice.html'
        elif type(question) == TruthTableQuestion:
            formula = Formula(question.formula)
            context['formula'] = formula
            context['truth_table'] = TruthTable(formula)
            self.template_name = 'logic/truth_table.html'
        return context

    def post(self, request, chnum, qnum):
        chapter = Chapter.objects.get(number=chnum)
        question = Question._get(chapter__number=chnum, number=qnum)
        ext_data = None

        # handle answer according to question type
        if type(question) == ChoiceQuestion:
            correct = self._handle_choice_post(request)
        elif type(question) == TruthTableQuestion:
            correct, ext_data = self._handle_truth_table_post(request, question)

        # register user answer
        user_chapter, _ = UserChapter.objects.get_or_create(
            user=request.user,
            chapter=chapter,
        )
        user_ans, created = UserAnswer.objects.get_or_create(
            user=request.user,
            chapter=chapter,
            user_chapter=user_chapter,
            question_number=question.number,
            defaults={'correct':correct},
        )

        # save only if value changed
        if user_ans.correct != correct:
            user_ans.correct = correct
            user_ans.save()

        # make a response
        response = {
            'correct' : user_ans.correct,
            'next_url' : ('location.href="%s";' % next_question_url(question.chapter, self.request.user)),
        }
        if ext_data:
            response.update(ext_data)
        print 'resp', response
        return JsonResponse(response)

    def _handle_choice_post(self, request):
        return Choice.objects.get(id=request.POST['choice']).is_correct

    def _handle_truth_table_post(self, request, question):
        formula = Formula(question.formula)
        values = [v == 'T' for v in request.POST.getlist('values[]')]
        option_correct = int(request.POST['option']) == formula.correct_option.num
        tt_correct = values == TruthTable(formula).result
        return (option_correct and tt_correct), {'tt_correct':tt_correct}


