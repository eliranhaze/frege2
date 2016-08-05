import ast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from itertools import groupby

from .formula import (
    Formula,
    FormulaSet,
    Argument,
    TruthTable,
    MultiTruthTable,
    formalize,
    formal_type,
)
from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
    Choice,
    FormulationQuestion,
    FormulationAnswer,
    TruthTableQuestion,
    DeductionQuestion,
    UserAnswer,
    ChapterSubmission,
)

import logging
logger = logging.getLogger(__name__)

def get_question_or_404(**kwargs):
    question = Question._get(**kwargs)
    if not question:
        raise Http404('Question does not exist: %s' % kwargs)
    return question

def next_question(chapter, user):
    questions = Question._filter(chapter=chapter)
    questions.sort(key=lambda q: q.number)
    for question in questions:
        if not question.user_answer(user):
            return question

    # check for unanswered followups
    for question in questions:
        if question.has_followup() and len(question.user_answer(user)) == 1:
            return question

    # all questions are answered, check if re-answering
    submission = ChapterSubmission.objects.filter(chapter=chapter, user=user).first()
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
    user_answers = {(ans.question_number, ans.is_followup) \
                    for ans in UserAnswer.objects.filter(user=user, chapter=chapter)}
    data = {}
    for q in chapter.questions():
        data[q.number] = (q.number, False) in user_answers
        if q.has_followup() and data[q.number]:
            if not (q.number, True) in user_answers:
                data[q.number] = 'half'
    return data

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        chapters = Chapter.objects.all()
        logger.debug('%s: %d chapters', self.request.user, len(chapters))
        return chapters

class AboutView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/about.html'
    def get_object(self):
        return None

class ChapterView(LoginRequiredMixin, generic.DetailView):

    def get_object(self):
        return get_object_or_404(Chapter, number=self.kwargs['chnum'])

    def dispatch(self, request, chnum):
        chapter = get_object_or_404(Chapter, number=chnum)
        logger.debug('%s: chapter %s', self.request.user, chapter)
        return HttpResponseRedirect(next_question_url(chapter, request.user))

class UserView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/user.html'

    def get_queryset(self):
        submissions = ChapterSubmission.objects.filter(user=self.request.user,time__isnull=False)
        logger.debug('%s: user view %d submissions', self.request.user, len(submissions))
        return submissions

#    def get_context_data(self, **kwargs):
#        context = super(UserView, self).get_context_data(**kwargs)
#        if not self.object_list:
#            # no submissions for user
#            return context
#
#        # average score for user
#        scores = [s.percent_correct() for s in self.object_list]
#        context['avg'] = sum(scores)/len(scores)
#
#        # stats per question type
#        answers = [a for s in self.object_list for a in s.useranswer_set.all()]
#        by_type = groupby(answers, lambda a: Question._get(number=a.question_number, chapter=a.submission.chapter).__class__.__name__)
#        stats = {}
#        for qtype, answers in by_type:
#            ans_list = [a for a in answers]
#            total, correct = stats.get(qtype, (0,0))
#            stats[qtype] = (total+len(ans_list), correct+len([a for a in ans_list if a.correct]))
#        stats = {t: int(round((100.*correct/total))) for t, (total,correct) in stats.iteritems() if total > 0}
#        context['stats'] = stats
#        return context

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
        logger.debug('%s: chapter %s summary', self.request.user, chapter)
        submission = ChapterSubmission.objects.filter(chapter=chapter, user=self.request.user).first()
        logger.debug('%s: fetched submission %s for context', self.request.user, submission)
        if submission and not submission.ongoing and submission.is_complete():
            answer_data, num_correct, pct = submission.correctness_data()
            sorted_answer_data = [(qnum, followup, correct) for (qnum, followup), correct in answer_data.iteritems()]
            sorted_answer_data.sort()
            context['answer_data'] = sorted_answer_data
            context['num_correct'] = num_correct
            context['pct'] = pct
            context['remaining'] = submission.max_attempts - submission.attempt
            logger.debug('%s: serving chapter %s summary, context=%r', self.request.user, chapter.number, context)
        else:
            logger.debug('%s: not serving chapter %s summary', self.request.user, chapter.number)
        return context

    def post(self, request, chnum):
        logger.info('%s: submitting chapter %s', request.user, chnum)
        chapter = Chapter.objects.get(number=chnum)
        submission = ChapterSubmission.objects.get(
            user=request.user,
            chapter=chapter,
        )
        logger.debug('%s: fetched submission %s for update', request.user, submission)
        response = {}
        if submission.is_complete() and submission.can_try_again() and submission.ongoing:
            submission.time = timezone.localtime(timezone.now())
            submission.attempt += 1
            submission.ongoing = False
            submission.save()
            logger.info('%s: saved submission: %s', self.request.user, submission)
            response['next'] = reverse('logic:chapter-summary', args=(chapter.number,))
        else:
            logger.info('%s: submission not allowed: %s', self.request.user, submission)
        logger.debug('%s: submission post response: %s', self.request.user, response)
        return JsonResponse(response)

class QuestionView(LoginRequiredMixin, generic.DetailView):
    template_name = 'logic/chapter.html'
    context_object_name = 'question'

    def __init__(self, *args, **kwargs):
        super(QuestionView, self).__init__(*args, **kwargs)
        
        # question type handlers
        self.context_handlers = {
            ChoiceQuestion: self._handle_choice_context,
            FormulationQuestion: self._handle_formulation_context,
            TruthTableQuestion: self._handle_truth_table_context,
            DeductionQuestion: self._handle_deduction_context,
        }
        self.post_handlers = {
            ChoiceQuestion: self._handle_choice_post,
            FormulationQuestion: self._handle_formulation_post,
            TruthTableQuestion: self._handle_truth_table_post,
            DeductionQuestion: self._handle_deduction_post,
        }

    def get_object(self):
        question = get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])
        logger.debug('%s: question %s', self.request.user, question._str)
        return question

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        question = self.object
        logger.debug('%s: question %s', self.request.user, question._str)
        context['chapter'] = question.chapter
        context['chap_questions'] = chapter_questions_user_data(question.chapter, self.request.user)

        # update submission data
        submission = ChapterSubmission.objects.filter(chapter=question.chapter, user=self.request.user).first()
        if submission:
            context['complete'] = submission.is_complete()
            context['remaining'] = submission.max_attempts - submission.attempt

        # update answer data
        answer = None
        user_answer = UserAnswer.objects.filter(
            user=self.request.user,
            chapter=question.chapter,
            question_number=question.number,
            is_followup = self._is_followup(),
        ).first()
        if user_answer:
            context['ans_time'] = user_answer.time
            answer = user_answer.answer
 
        # update context according to type
        context.update(
            self.context_handlers[type(question)](question, answer)
        )
        logger.debug('%s: serving question %s/%s, context=%s', self.request.user, question.chapter.number, question.number, context)
        return context

    def post(self, request, chnum, qnum):
        logger.info('%s: answering question %s/%s', request.user, chnum, qnum)

        chapter = Chapter.objects.get(number=chnum)
        question = Question._get(chapter__number=chnum, number=qnum)
        ext_data = None

        # handl user submission
        submission, created = ChapterSubmission.objects.get_or_create(
            user=request.user,
            chapter=chapter,
            defaults={
                'attempt':0,
                'ongoing':True,
            },
        )
        logger.debug('%s: fetched submission %s, created=%s', request.user, submission, created)

        if not submission.can_try_again():
            return JsonResponse({})

        if not submission.ongoing:
            logger.debug('%s: submission is now ongoing', request.user)
            submission.ongoing = True
            submission.save()

        # handle answer according to question type
        correct, ext_data, answer = self.post_handlers[type(question)](request, question)

        # register user answer
        user_ans, created = UserAnswer.objects.get_or_create(
            user=request.user,
            chapter=question.chapter,
            submission=submission,
            question_number=question.number,
            is_followup = self._is_followup(),
            defaults={
                'correct': correct,
                'answer': answer,
                'time': timezone.localtime(timezone.now()),
            },
        )

        # save user answer
        if not created:
            user_ans.correct = correct
            user_ans.answer = answer
            user_ans.time = timezone.localtime(timezone.now())
            user_ans.save()

        logger.info('%s: %s answer %s/%s, correct=%s', request.user, 'saved new' if created else 'updated', chnum, qnum, correct)

        # make a response
        response = {
            'complete': submission.is_complete(),
            'next': 'location.href="%s";' % self._next_url(request, question),
        }
        if ext_data:
            response.update(ext_data)
        logger.debug('%s: question post response: %s', request.user, response)
        return JsonResponse(response)

    def _next_url(self, request, question):
        if question.has_followup():
            return reverse('logic:followup', args=(question.chapter.number, question.number))
        else:
            return next_question_url(question.chapter, request.user)

    def _is_followup(self):
        return self.__class__ == FollowupQuestionView

    # ========================
    # Question types
    # ========================

    def _handle_choice_context(self, question, answer):
        self.template_name = 'logic/choice.html'
        return {'answer':int(answer)} if answer else {}

    def _handle_choice_post(self, request, *args):
        choice = request.POST['choice']
        logger.debug('%s: checking choice %s', request.user, choice)
        return Choice.objects.get(id=choice).is_correct, None, str(choice)

    def _handle_formulation_context(self, question, answer):
        self.template_name = 'logic/formulation.html'
        ans_type = formal_type(FormulationAnswer.objects.filter(question=self.object).first().formula)
        context = {
            'type': ans_type.__name__,
        }
        if answer:
            context['answer'] = answer
        return context

    def _handle_formulation_post(self, request, question):
        is_correct = False
        answer = request.POST['formulation']
        logger.debug('%s: checking formulation %s', request.user, answer)
        formalized = formalize(answer)
        for correct_ans in FormulationAnswer.objects.filter(question=question):
            if formalize(correct_ans.formula) == formalized:
                is_correct = True
                break
        return is_correct, None, answer

    def _handle_truth_table_context(self, question, answer):
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
        if answer:
            answer_tt, answer_option = answer.split('#')
            context['answer'] = ast.literal_eval(answer_tt)
            context['answer_option'] = int(answer_option)
        return context

    def _handle_truth_table_post(self, request, question):
        answers = []
        for i in xrange(1000):
            l = request.POST.getlist('values[%d][]' % i)
            if not l:
                break
            answers.append(l)
        boolean_answers = [[v == 'T' for v in values] for values in answers]
        logger.debug('%s: checking truth table answers %s', request.user, boolean_answers)
 
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
        tt_corrects = [answer_values == result_values for answer_values, result_values in zip(boolean_answers, truth_table.result)]
        user_option = int(request.POST['option'])
        logger.debug('%s: checking truth table option %s', request.user, user_option)
        option_correct = user_option == correct_option.num

        answer = '%s#%s' % (str(answers), user_option)
        return (option_correct and all(tt_corrects)), {'tt_corrects':tt_corrects}, answer

    def _handle_deduction_context(self, question, answer):
        self.template_name = 'logic/deduction.html'
        argument = Argument(question.formula)
        context = {
            'argument': argument,
            'premises': argument.premises,
        }
        if answer:
            context['answer'] = answer
        return context

    def _handle_deduction_post(self, request, question):
        argument = Argument(question.formula)
        conclusion = request.POST['conclusion']
        logger.debug('%s: checking deduction conclusion %s', request.user, conclusion)
        return Formula(conclusion) == argument.conclusion, None, request.POST['obj']

class FollowupQuestionView(QuestionView):

    def _get_answer(self, question):
        return UserAnswer.objects.filter(
            user=self.request.user,
            chapter=question.chapter,
            question_number=question.number
        ).first()

    def dispatch(self, request, chnum, qnum):
        question = get_question_or_404(chapter__number=chnum, number=qnum)
        if not question.has_followup() or self._get_answer(question) is None:
            # no followup
            return HttpResponseRedirect(reverse('logic:question', args=(chnum, qnum)))
        return super(FollowupQuestionView, self).dispatch(request, chnum, qnum)

    def get_object(self):
        original = get_question_or_404(chapter__number=self.kwargs['chnum'], number=self.kwargs['qnum'])
        if original.followup == FormulationQuestion.TRUTH_TABLE:
            followup = TruthTableQuestion()
        elif original.followup == FormulationQuestion.DEDUCTION:
            followup = DeductionQuestion()
        else:
            raise ValueError('invalid followup type %r in question %s' % (original.followup, original)) 
        followup.chapter = original.chapter
        followup.number = original.number
        followup.formula = self._get_answer(original).answer
        if type(followup) == TruthTableQuestion:
            followup._set_table_type()

        logger.debug('%s: followup question is %s %s', self.request.user, type(followup).__name__, followup)
        return followup

    def get_context_data(self, **kwargs):
        context = super(FollowupQuestionView, self).get_context_data(**kwargs)
        context['followup'] = True
        return context

    def _next_url(self, request, question):
        return next_question_url(question.chapter, request.user)

    def _handle_formulation_post(self, request, question):
        if question.followup == FormulationQuestion.TRUTH_TABLE:
            handler = self._handle_truth_table_post
        elif question.followup == FormulationQuestion.DEDUCTION:
            handler = self._handle_deduction_post
        else:
            raise ValueError('invalid followup type %r in question %s' % (question.followup, question)) 
        return handler(request, self.get_object())

