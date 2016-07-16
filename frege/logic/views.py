from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .formula import (
    Formula,
    FormulaSet,
    Argument,
    TruthTable,
    MultiTruthTable,
)
from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
    Choice,
    TruthTableQuestion,
    DeductionQuestion,
    UserAnswer,
    ChapterSubmission,
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

    # all questions are answered, check if re-answering
    submission = ChapterSubmission.objects.filter(chapter=chapter).first()
    if submission and submission.ongoing:
        return chapter.first_question()

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

    def dispatch(self, request):
        ip = request.META['HTTP_X_FORWARDED_FOR'] if 'HTTP_X_FORWARDED_FOR' in request.META else None
        agent = request.META['HTTP_USER_AGENT'] if 'HTTP_USER_AGENT' in request.META else None
        if ip and agent:
            print 'USER', request.user, 'IP', ip, 'AGENT', agent
        return super(IndexView, self).dispatch(request)

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

    def dispatch(self, request, chnum):
        chapter = get_object_or_404(Chapter, number=chnum)
        if chapter.num_questions() == 0:
            return HttpResponseRedirect(reverse('logic:index'))
        return super(ChapterSummaryView, self).dispatch(request, chnum)

    def get_context_data(self, **kwargs):
        context = super(ChapterSummaryView, self).get_context_data(**kwargs)
        chapter = self.object
        chap_questions = chapter_questions_user_data(chapter, self.request.user)
        submission = ChapterSubmission.objects.filter(chapter=chapter).first()
        if submission and not submission.ongoing and submission.is_complete():
            context['num_correct'] = sum(1 for _, correct in chap_questions.iteritems() if correct)
            context['chap_questions'] = chap_questions
            context['pct'] = submission.percent_correct()
            context['remaining'] = submission.max_attempts - submission.attempt
        return context

    def post(self, request, chnum):
        chapter = Chapter.objects.get(number=chnum)
        submission = ChapterSubmission.objects.get(
            user=request.user,
            chapter=chapter,
        )
        response = {}
        if submission.is_complete() and submission.can_try_again():
            submission.attempt += 1
            submission.ongoing = False
            submission.save()
            response['next'] = reverse('logic:chapter-summary', args=(chapter.number,))
        return JsonResponse(response)

class QuestionView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'
    context_object_name = 'question'

    def __init__(self, *args, **kwargs):
        super(QuestionView, self).__init__(*args, **kwargs)
        
        # question type handlers
        self.context_handlers = {
            ChoiceQuestion : self._handle_choice_context,
            TruthTableQuestion : self._handle_truth_table_context,
            DeductionQuestion : self._handle_deduction_context,
        }
        self.post_handlers = {
            ChoiceQuestion : self._handle_choice_post,
            TruthTableQuestion : self._handle_truth_table_post,
            DeductionQuestion : self._handle_deduction_post,
        }

    def get_object(self):
        return get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        question = self.object
        context['chapter'] = question.chapter
        context['chap_questions'] = chapter_questions_user_data(question.chapter, self.request.user)
        submission = ChapterSubmission.objects.filter(chapter=question.chapter).first()
        if submission:
            context['remaining'] = submission.max_attempts - submission.attempt
        context.update(
            self.context_handlers[type(question)](question)
        )
        return context

    def post(self, request, chnum, qnum):
        chapter = Chapter.objects.get(number=chnum)
        question = Question._get(chapter__number=chnum, number=qnum)
        ext_data = None

        # handl user submission
        submission, _ = ChapterSubmission.objects.get_or_create(
            user=request.user,
            chapter=chapter,
            defaults={
                'attempt':0,
                'ongoing':True,
            },
        )

        if not submission.can_try_again():
            return JsonResponse({})

        if not submission.ongoing:
            submission.ongoing = True
            submission.save()

        # handle answer according to question type
        correct, ext_data = self.post_handlers[type(question)](request, question)

        # register user answer
        user_ans, created = UserAnswer.objects.get_or_create(
            user=request.user,
            chapter=chapter,
            submission=submission,
            question_number=question.number,
            defaults={'correct':correct},
        )

        # save only if value changed
        if user_ans.correct != correct:
            user_ans.correct = correct
            user_ans.save()

        # make a response
        response = {
            'complete': submission.is_complete(),
            'next': ('location.href="%s";' % next_question_url(question.chapter, self.request.user)),
        }
        if ext_data:
            response.update(ext_data)
        return JsonResponse(response)

    # ========================
    # Question types
    # ========================

    def _handle_choice_context(self, *args):
        self.template_name = 'logic/choice.html'
        return {}

    def _handle_choice_post(self, request, *args):
        return Choice.objects.get(id=request.POST['choice']).is_correct, None

    def _handle_truth_table_context(self, question):
        self.template_name = 'logic/truth_table.html'
        context = {}
        if question.is_formula:
            formulas = [Formula(question.formula)]
            options = formulas[0].options
        elif question.is_set:
            formulas = FormulaSet(question.formula)
            options = formulas.options
        elif question.is_argument:
            formulas = Argument(question.formula)
            options = formulas.options
        context['formulas'] = formulas
        context['truth_table'] = MultiTruthTable(formulas)
        context['options'] = options
        return context

    def _handle_truth_table_post(self, request, question):
        answers = []
        for i in xrange(1000):
            l = request.POST.getlist('values[%d][]' % i)
            if not l:
                break
            answers.append(l)
        answers = [[v == 'T' for v in values] for values in answers]
  
        if question.is_formula:
            formulas = [Formula(question.formula)]
            correct_option = formulas[0].correct_option
        elif question.is_set:
            formulas = FormulaSet(question.formula)
            correct_option = formulas.correct_option
        elif question.is_argument:
            formulas = Argument(question.formula)
            correct_option = formulas.correct_option

        truth_table = MultiTruthTable(formulas)
        tt_corrects = [answer_values == result_values for answer_values, result_values in zip(answers, truth_table.result)]
        option_correct = int(request.POST['option']) == correct_option.num

        return (option_correct and all(tt_corrects)), {'tt_corrects':tt_corrects}

    def _handle_deduction_context(self, question):
        self.template_name = 'logic/deduction.html'
        argument = Argument(question.formula)
        context = {
            'argument': argument,
            'premises': argument.premises,
        }
        return context

    def _handle_deduction_post(self, request, question):
        argument = Argument(question.formula)
        return Formula(request.POST['conclusion']) == argument.conclusion, None
