# -*- coding: utf-8 -*-
import json

from datetime import datetime, timedelta
from itertools import groupby

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase

from .formula import (
    Formula,
    PredicateFormula,
    TruthTable,
    MultiTruthTable,
    FormulaSet,
    Argument,
    NEG,
    CON,
    DIS,
    IMP,
    EQV,
    ALL,
    EXS,
    Tautology,
    Contingency,
    Contradiction,
    quantifier_range,
)

from .models import (
    Chapter,
    Question,
    ChoiceQuestion,
    Choice,
    OpenQuestion,
    FormulationQuestion,
    FormulationAnswer,
    TruthTableQuestion,
    ModelQuestion,
    DeductionQuestion,
    UserAnswer,
    OpenAnswer,
    ChapterSubmission,
)

def login(self):
    u = User.objects.create_superuser('u', 'u@hi.com', 'pw')
    self.user = u
    self.client.login(username = 'u', password = 'pw')

def create_user_answer(q, **kw):
    a = UserAnswer(**kw)
    a.set_question(q)
    a.save()
    return a

class IndexViewTests(TestCase):

    def setUp(self):
        login(self)

    def _create_for_chapters(self, chapters):
        for c in chapters:
            TruthTableQuestion.objects.create(chapter=c, number=1, formula='p')

    def _assertHas(self, response, chapters):
        self.assertQuerysetEqual(response.context['chapter_list'], [repr(c) for c in chapters])
        for chapter in chapters:
            self.assertContains(response, chapter.title)

    def test_index_view_no_chapters(self):
        response = self.client.get(reverse('logic:index'))
        self.assertContains(response, 'No chapters are available')
        self.assertQuerysetEqual(response.context['chapter_list'], [])

    def test_index_one_chapter(self):
        chapters = [Chapter.objects.create(title='chapternum1', number=1)]
        self._create_for_chapters(chapters)
        response = self.client.get(reverse('logic:index'))
        self._assertHas(response, chapters)
 
    def test_index_many_chapters(self):
        chapters = [Chapter.objects.create(title='chapternum%s'%i, number=i) for i in range(1,6)]
        self._create_for_chapters(chapters)
        response = self.client.get(reverse('logic:index'))
        self._assertHas(response, chapters)

class QuestionViewTests(TestCase):
 
    def setUp(self):
        self.chapter = Chapter.objects.create(title='chap', number=1)
        login(self)

    def _create_choice_question(self, number=1, num_choices=1):
        q = ChoiceQuestion.objects.create(chapter=self.chapter, number=number, text='hithere')
        choices = []
        for i in range(num_choices):
            choices.append(Choice.objects.create(question=q, text='choicenum%s'%i, is_correct=(i==1)))
        return q, choices

    def _create_formulation_question(self, number=1, ans=[], followup=False):
        q = FormulationQuestion.objects.create(
            chapter=self.chapter,
            number=number,
            text='hithere',
            followup=FormulationQuestion.DEDUCTION if followup else FormulationQuestion.NONE,
        )
        answers = [
            FormulationAnswer.objects.create(
                question=q,
                formula=a,
            ) for a in ans
        ]
        return q, answers

    def _get_url(self, question):
        return reverse('logic:question', args=(question.chapter.number, question.number))

    def _get_view(self, question):
        return self.client.get(self._get_url(question))

    def _assertHas(self, response, choices):
        for choice in choices:
            self.assertContains(response, choice.text)

    def _assertQuestion(self, response, question):
        self.assertEquals(question, response.context['question'])
        self.assertEquals(question.chapter, response.context['chapter'])

    def _assertJSON(self, response, data):
        for k, v in data.iteritems():
            self.assertEquals(response.json()[k], v)

    def _post_choice(self, question, choice, allowed=True):
        response = self.client.post(self._get_url(question), {'choice':choice.id})
        self.assertTrue(allowed == ('next' in response.json()))

    def _post_followup(self, question, conclusion, allowed=True):
        response = self.client.post(
            reverse('logic:followup', args=(question.chapter.number, question.number)),
            {'conclusion':conclusion, 'obj':''}
        )
        self.assertTrue(allowed == ('next' in response.json()))

    def _post_formulation(self, question, answer, allowed=True):
        response = self.client.post(self._get_url(question), {'formulation':answer})
        self.assertTrue(allowed == ('next' in response.json()))

    def _post_submission(self, allowed):
        response = self.client.post(reverse('logic:chapter-summary', args=(self.chapter.number,)))
        self.assertTrue(allowed == ('next' in response.json()))

    def _get_submission(self, allowed):
        response = self.client.get(reverse('logic:chapter-summary', args=(self.chapter.number,)))
        if allowed:
            self.assertContains(response, 'ענית נכון')
            self.assertNotContains(response, 'russell')
        else:
            self.assertContains(response, 'russell')
            self.assertNotContains(response, 'ענית נכון')

    def test_choice_question(self):
        q, choices = self._create_choice_question(num_choices=5)
        response = self._get_view(q)
        self._assertQuestion(response, q)
        self._assertHas(response, choices)

    def test_choice_question_post(self):
        q, choices = self._create_choice_question(num_choices=5)
        # make sure choices are created property for this test
        assert any(c.is_correct for c in choices)
        assert any(not c.is_correct for c in choices)
        # post and check every choice
        for is_correct, group in groupby(choices, lambda c: c.is_correct):
            for choice in group:
                self._post_choice(q, choice)
            self.assertEquals(len(q.user_answers()), 1)
            self.assertEquals(q.user_answers().first().correct, is_correct)
        self.assertEquals(len(ChapterSubmission.objects.filter(chapter=self.chapter,user=self.user)), 1)

    def test_chapter_submission(self):
        # create questions
        q1, choices1 = self._create_choice_question(number=1, num_choices=3)
        q2, choices2 = self._create_choice_question(number=2, num_choices=3)
        q3, choices3 = self._create_choice_question(number=3, num_choices=3)

        # post answers
        self._post_choice(q1, choices1[1]) # correct
        self._get_submission(allowed=False)
        self._post_choice(q2, choices2[0]) # incorrect
        self._post_submission(allowed=False)
        self._post_choice(q3, choices3[0]) # incorrect
        self._post_submission(allowed=True)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 1)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), True)
        self.assertEquals(cs.percent_correct(), 33)

        # 2nd attempt
        self._post_choice(q2, choices2[1]) # correct
        self._get_submission(allowed=False)
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.ongoing, True)
        self.assertEquals(cs.is_complete(), True)
        self._post_choice(q3, choices3[2]) # incorrect
        self._get_submission(allowed=False)
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.ongoing, True)
        self.assertEquals(cs.is_complete(), True)
        self._post_submission(allowed=True)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 2)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), True)
        self.assertEquals(cs.percent_correct(), 67)
        self._get_submission(allowed=True)

        # 3rd attempt
        self._post_choice(q3, choices3[1]) # correct
        self._get_submission(allowed=False)
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.ongoing, True)
        self.assertEquals(cs.is_complete(), True)
        self._post_submission(allowed=True)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 3)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), False)
        self.assertEquals(cs.percent_correct(), 100)

        # illegal attempt
        self._post_choice(q3, choices3[1], allowed=False)
        self._get_submission(allowed=True)

    def test_chapter_submission_followups(self):
        # create questions
        q1, choices1 = self._create_choice_question(number=1, num_choices=3)
        q2, answers2 = self._create_formulation_question(number=2, ans=[u'p∴p',u'q∴q'], followup=True)
        q3, answers3 = self._create_formulation_question(number=3, ans=[u'~(p%sq)∴~q' % DIS,u'~q%s~p∴~p' % CON], followup=True)
        q4, answers4 = self._create_formulation_question(number=4, ans=['~Ra','~Sa'], followup=False)

        # post answers
        self._post_choice(q1, choices1[1]) # correct
        self._get_submission(allowed=False)
        self._post_formulation(q2, u'~p∴p') # incorrect
        self._post_submission(allowed=False)
        self._post_followup(q2, u'~p') # incorrect (followup)
        self._post_submission(allowed=False)
        self._get_submission(allowed=False)
        self._post_submission(allowed=False)
        self._post_submission(allowed=False)
        self._post_formulation(q3, u'~p%s~q∴~p' % CON) # correct, followup skipped
        self._get_submission(allowed=False)
        self._post_submission(allowed=False)
        self._post_formulation(q4, u'Ra') # incorrect
        self._post_submission(allowed=False)
        self._post_followup(q3, u'~p') # correct (followup)
        self._post_submission(allowed=True)
        self._post_submission(allowed=False)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 1)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), True)
        self.assertEquals(cs.percent_correct(), 50) # 3/6

        # 2nd attempt
        self._post_formulation(q2, u'p∴p') # correct
        self._get_submission(allowed=False)
        self._post_followup(q2, u'~p') # incorrect (followup)
        self._get_submission(allowed=False)
        self._post_formulation(q4, u'~Rb') # incorrect
        self._get_submission(allowed=False)
        self._post_submission(allowed=True)
        self._post_submission(allowed=False)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 2)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), True)
        self.assertEquals(cs.percent_correct(), 67) # 4/6

        # 3rd attempt
        self._post_formulation(q2, u'p∴p') # correct
        self._get_submission(allowed=False)
        self._post_followup(q2, u'p') # correct (followup)
        self._get_submission(allowed=False)
        self._post_formulation(q4, u'~Sa') # correct
        self._get_submission(allowed=False)
        self._post_submission(allowed=True)
        self._post_submission(allowed=False)

        # check submission
        cs = ChapterSubmission.objects.get(chapter=self.chapter, user=self.user)
        self.assertEquals(cs.attempt, 3)
        self.assertEquals(cs.ongoing, False)
        self.assertEquals(cs.is_complete(), True)
        self.assertEquals(cs.can_try_again(), False)
        self.assertEquals(cs.percent_correct(), 100) # 6/6

        # illegal attempt
        self._post_formulation(q2, u'p∴p', allowed=False)
        self._get_submission(allowed=True)

class QuestionTests(TestCase):

    def test_clean_duplicate_number(self):
        chapter = Chapter.objects.create(title='chap', number=1)
        qc = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        # create another question with the same number and assert error
        qo = OpenQuestion(chapter=chapter, text='hi?', number=1)
        self.assertRaises(ValidationError, qo.clean)
        # create it in another chapter, this should be ok
        chapter = Chapter.objects.create(title='chap', number=2)
        qo = OpenQuestion(chapter=chapter, text='hi?', number=1)
        qo.clean()
        
    def test_query_all(self):
        chapter = Chapter.objects.create(title='chap', number=1)
        chapter_open = Chapter.objects.create(title='chap', number=2)
        qc = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        qo = OpenQuestion.objects.create(chapter=chapter_open, text='hi?', number=2)
        qf = FormulationQuestion.objects.create(chapter=chapter, text='hi?', number=3)
        qt = TruthTableQuestion.objects.create(chapter=chapter, formula='p%sq'%DIS, number=4)
        qm = ModelQuestion.objects.create(chapter=chapter, formula='Pa', number=5)
        qd = DeductionQuestion.objects.create(chapter=chapter, formula=u'p%sq∴p'%CON, number=6)
        self.assertItemsEqual(Question._all(), [qc, qo, qf, qt, qm, qd])
        self.assertItemsEqual(Question._filter(chapter=chapter), [qc, qf, qt, qm, qd])
        self.assertItemsEqual(Question._filter(chapter=chapter_open), [qo])
        self.assertItemsEqual(Question._filter(number=6), [qd])
        self.assertEqual(Question._get(number=6), qd)
        self.assertEqual(Question._count(), 6)

class ChapterTests(TestCase):

    def test_is_open_empty(self):
        chapter = Chapter.objects.create(title='ch', number=1)
        self.assertFalse(chapter.is_open())

    def test_is_open_yes(self):
        chapter = Chapter.objects.create(title='ch', number=1)
        OpenQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        OpenQuestion.objects.create(chapter=chapter, text='hi2?', number=2)
        self.assertTrue(chapter.is_open())

    def test_is_open_no(self):
        chapter = Chapter.objects.create(title='ch', number=1)
        ModelQuestion.objects.create(chapter=chapter, formula='Pa', number=1)
        DeductionQuestion.objects.create(chapter=chapter, formula=u'p%sq∴p'%CON, number=2)
        self.assertFalse(chapter.is_open())

class ChapterSubmissionTests(TestCase):

    def create_submission(self, chapter, user):
        return ChapterSubmission.objects.create(chapter=chapter,user=user,attempt=0,ongoing=False)

    def test_percent_correct(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        # with 1 question
        q = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        cs = self.create_submission(chapter, user)
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=False)
        self.assertEquals(cs.percent_correct(), 0)
        ua.correct = True
        ua.save()
        self.assertEquals(cs.percent_correct(), 100)
        # 2nd question
        q2 = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        ua2 = create_user_answer(q=q2, chapter=chapter,user=user,submission=cs, correct=False)
        self.assertEquals(cs.percent_correct(), 50)
        ua2.correct = True
        ua2.save()
        self.assertEquals(cs.percent_correct(), 100)

    def test_is_complete(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)

        # no questions
        cs = self.create_submission(chapter, user)
        self.assertTrue(cs.is_complete())

        # with 1 question
        q = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=False)
        self.assertTrue(cs.is_complete())

        # 2nd question
        q2 = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q2, chapter=chapter,user=user,submission=cs, correct=True)
        self.assertTrue(cs.is_complete())

    def test_is_complete_followups(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        cs = self.create_submission(chapter, user)

        # with 1 question + followup
        q = FormulationQuestion.objects.create(chapter=chapter, text='hi?', number=1, followup=FormulationQuestion.DEDUCTION)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=True, is_followup=False)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=False, is_followup=True)
        self.assertTrue(cs.is_complete())

        # 2nd question
        q2 = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q2, chapter=chapter,user=user,submission=cs, correct=True)
        self.assertTrue(cs.is_complete())

        # 3rd question + followup
        q3 = FormulationQuestion.objects.create(chapter=chapter, text='hi?', number=3, followup=FormulationQuestion.DEDUCTION)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q3, chapter=chapter,user=user,submission=cs, correct=False, is_followup=False)
        self.assertFalse(cs.is_complete())
        ua = create_user_answer(q=q3, chapter=chapter,user=user,submission=cs, correct=False, is_followup=True)
        self.assertTrue(cs.is_complete())

    def test_is_ready_no_open(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        cs = self.create_submission(chapter, user)

        # with 1 non-open question
        q = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        self.assertFalse(cs.is_ready())
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=False)
        self.assertTrue(cs.is_ready())

    def test_is_ready_open(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        cs = self.create_submission(chapter, user)

        # with 1 non-open question
        q = OpenQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        self.assertFalse(cs.is_ready())
        ua = create_user_answer(q=q, chapter=chapter,user=user,submission=cs, correct=False)
        oa = OpenAnswer.objects.create(text='x', question=q, user_answer=ua)
        self.assertFalse(cs.is_ready())
        oa.grade = 1.
        oa.save()
        self.assertTrue(cs.is_ready())

    def test_is_ready_many_open(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        cs = self.create_submission(chapter, user)

        q1 = OpenQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        q2 = OpenQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        q3 = OpenQuestion.objects.create(chapter=chapter, text='hi?', number=3)
 
        def _create_answer(question):
            ua = create_user_answer(q=question, chapter=chapter,user=user,submission=cs, correct=False)
            oa = OpenAnswer.objects.create(text='x', question=question, user_answer=ua)
            return oa

        def _check(answer):
            answer.grade = 1.
            answer.save()
           
        self.assertFalse(cs.is_ready())
        oa1 = _create_answer(q1)
        self.assertFalse(cs.is_ready())
        _check(oa1)
        self.assertFalse(cs.is_ready())

        oa2 = _create_answer(q2)
        self.assertFalse(cs.is_ready())
        _check(oa2)
        self.assertFalse(cs.is_ready())

        oa3 = _create_answer(q3)
        self.assertFalse(cs.is_ready())
        _check(oa3)
        self.assertTrue(cs.is_ready())

class FormulaTests(TestCase):

    def test_strip(self):
        f = Formula('p')
        self.assertEquals(f._strip('p'), 'p')
        self.assertEquals(f._strip('(p)'), 'p')
        self.assertEquals(f._strip('((p))'), 'p')
        self.assertEquals(f._strip('(((p)))'), 'p')
        self.assertEquals(f._strip('(p.q).p'), '(p.q).p')
        self.assertEquals(f._strip('((p.q).p)'), '(p.q).p')
        self.assertEquals(f._strip('(((p.q).p))'), '(p.q).p')

    def test_analyze_atomic(self):
        f = Formula('p')
        self.assertEquals(f.con, None)
        self.assertEquals(f.sf1, None)
        self.assertEquals(f.sf2, None)
        self.assertEquals(f.literal, 'p')

    def test_analyze_atomic2(self):
        f = Formula('(p)')
        self.assertEquals(f.con, None)
        self.assertEquals(f.sf1, None)
        self.assertEquals(f.sf2, None)
        self.assertEquals(f.literal, 'p')

    def test_analyze_simple(self):
        literal = 'p%sq' % CON
        f = Formula(literal)
        self.assertEquals(f.con, CON)
        self.assertEquals(f.sf1.literal, 'p')
        self.assertEquals(f.sf2.literal, 'q')
        self.assertEquals(f.literal, literal)

    def test_analyze_simple_upper(self):
        literal = 'P%sQ' % CON
        f = Formula(literal)
        self.assertEquals(f.con, CON)
        self.assertEquals(f.sf1.literal, 'P')
        self.assertEquals(f.sf2.literal, 'Q')
        self.assertEquals(f.literal, literal)

    def test_analyze_simple2(self):
        literal = 'p%sq' % IMP
        f = Formula('(%s)' % literal)
        self.assertEquals(f.con, IMP)
        self.assertEquals(f.sf1.literal, 'p')
        self.assertEquals(f.sf2.literal, 'q')
        self.assertEquals(f.literal, literal)

    def test_analyze_neg(self):
        literal = '%s%sp' % (NEG, NEG)
        f = Formula('(%s)' % literal)
        self.assertEquals(f.con, NEG)
        self.assertEquals(f.sf1.con, NEG)
        self.assertEquals(f.sf1.literal, '%sp' % NEG)
        self.assertEquals(f.sf1.sf1.literal, 'p')
        self.assertEquals(f.sf2, None)
        self.assertEquals(f.literal, literal)

    def test_analyze_with_brackets(self):
        literal = '(p)%s((q))' % IMP
        f = Formula('((%s))' % literal)
        self.assertEquals(f.con, IMP)
        self.assertEquals(f.sf1.literal, 'p')
        self.assertEquals(f.sf2.literal, 'q')
        self.assertEquals(f.literal, literal)

    def test_analyze_with_spaces(self):
        self.assertEquals(Formula('%s%sp' % (NEG, NEG)), Formula(' %s %sp ' % (NEG, NEG)))
        self.assertEquals(
            Formula('%s(q%sp)%s(r%sq)' % (NEG, EQV, IMP, DIS)),
            Formula(' %s (q  %sp)%s (r%sq )' % (NEG, EQV, IMP, DIS))
        )

    def test_analyze_ok(self):
        Formula('q%s%s%s%sp' % (CON, NEG, NEG, NEG))
        Formula('q%s(%s%s%sp)' % (CON, NEG, NEG, NEG))

    def test_analyze_complex(self):
        literal = '(%s(p%sq)%sp)%sr' % (NEG, IMP, CON, DIS)
        f = Formula('(%s)' % literal)
       
        # formula 
        self.assertEquals(f.con, DIS)
        self.assertEquals(f.sf1.literal, '%s(p%sq)%sp' % (NEG, IMP, CON))
        self.assertEquals(f.sf2.literal, 'r')
        self.assertEquals(f.literal, literal)

        # sub-formula 1
        self.assertEquals(f.sf1.sf1.literal, '%s(p%sq)' % (NEG, IMP))
        self.assertEquals(f.sf1.con, CON)
        self.assertEquals(f.sf1.sf2.literal, 'p')

        # sub-sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.literal, 'p%sq' % IMP)
        self.assertEquals(f.sf1.sf1.con, NEG)
        self.assertEquals(f.sf1.sf1.sf2, None)

        # sub-sub-sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.sf1.literal, 'p')
        self.assertEquals(f.sf1.sf1.sf1.con, IMP)
        self.assertEquals(f.sf1.sf1.sf1.sf2.literal, 'q')

    def test_analyze_complex_neg(self):
        literal = '((%s%s%sp%sq)%s%sp)%sr' % (NEG, NEG, NEG, IMP, CON, NEG, DIS)
        f = Formula('(%s)' % literal)
       
        # formula 
        self.assertEquals(f.con, DIS)
        self.assertEquals(f.sf1.literal, '(%s%s%sp%sq)%s%sp' % (NEG, NEG, NEG, IMP, CON, NEG))
        self.assertEquals(f.sf2.literal, 'r')
        self.assertEquals(f.literal, literal)

        # sub-formula 1
        self.assertEquals(f.sf1.sf1.literal, '%s%s%sp%sq' % (NEG, NEG, NEG, IMP))
        self.assertEquals(f.sf1.con, CON)
        self.assertEquals(f.sf1.sf2.literal, '%sp' % NEG)

        # sub-formula 1 sub-formula 2
        self.assertEquals(f.sf1.sf2.sf1.literal, 'p')
        self.assertEquals(f.sf1.sf2.con, NEG)
        self.assertEquals(f.sf1.sf2.sf2, None)

        # sub-formula 1 sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.literal, '%s%s%sp' % (NEG, NEG, NEG))
        self.assertEquals(f.sf1.sf1.con, IMP)
        self.assertEquals(f.sf1.sf1.sf2.literal, 'q')

        # sub-formula 1 sub-formula 1 sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.sf1.literal, '%s%sp' % (NEG, NEG))
        self.assertEquals(f.sf1.sf1.sf1.con, NEG)
        self.assertEquals(f.sf1.sf1.sf1.sf2, None)

        # sub-formula 1 sub-formula 1 sub-formula 1 sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.sf1.sf1.literal, '%sp' % NEG)
        self.assertEquals(f.sf1.sf1.sf1.sf1.con, NEG)
        self.assertEquals(f.sf1.sf1.sf1.sf1.sf2, None)

        # sub-formula 1 sub-formula 1 sub-formula 1 sub-formula 1 sub-formula 1
        self.assertEquals(f.sf1.sf1.sf1.sf1.sf1.sf1.literal, 'p')
        self.assertEquals(f.sf1.sf1.sf1.sf1.sf1.con, NEG)
        self.assertEquals(f.sf1.sf1.sf1.sf1.sf1.sf2, None)

    def test_analyze_empty(self):
        self.assertRaises(ValueError, Formula, '')
        self.assertRaises(ValueError, Formula, ' ')
        self.assertRaises(ValueError, Formula, '  ')

    def test_analyze_nonlatin(self):
        self.assertRaises(ValueError, Formula, '1')
        self.assertRaises(ValueError, Formula, '~2')
        self.assertRaises(ValueError, Formula, '1%s#' % CON)
        self.assertRaises(ValueError, Formula, u'ש')
        self.assertRaises(ValueError, Formula, u'~ש')
        self.assertRaises(ValueError, Formula, u'א%sב' % CON)
        self.assertRaises(ValueError, Formula, 'ש')
        self.assertRaises(ValueError, Formula, '~ש')

    def test_analyze_invalid(self):
        self.assertRaises(ValueError, Formula, 'pq')
        self.assertRaises(ValueError, Formula, '%sp' % IMP)
        self.assertRaises(ValueError, Formula, 'p%s' % IMP)
        self.assertRaises(ValueError, Formula, 'p%s' % NEG)
        self.assertRaises(ValueError, Formula, 'p%sq' % NEG)
        self.assertRaises(ValueError, Formula, '((p%sq)' % CON)
        self.assertRaises(ValueError, Formula, '(p%sq))' % CON)
        self.assertRaises(ValueError, Formula, '(((p%sq))' % CON)
        self.assertRaises(ValueError, Formula, '(p%sq%sr)' % (CON, CON))
        self.assertRaises(ValueError, Formula, '%s%s%s%sq' % (CON, DIS, IMP, EQV))
        self.assertRaises(ValueError, Formula, '(p%s%s%s%sq)' % (CON, DIS, IMP, EQV))
        self.assertRaises(ValueError, Formula, '(p%sq)%sq%sr' % (CON, CON, CON))
        self.assertRaises(ValueError, Formula, '(p%sq)%sq' % (CON, NEG))
        self.assertRaises(ValueError, Formula, '(p%sq)%s(q%sr)%sp' % (CON, CON, CON, CON))
        self.assertRaises(ValueError, Formula, '(p%sq)%s(q%sr)%s%sp' % (CON, CON, CON, CON, NEG))
        self.assertRaises(ValueError, Formula, 'p%s(p%sq)%s(q%sr)' % (CON, CON, CON, CON))
        self.assertRaises(ValueError, Formula, '((r%sq)%sp)%s(p%sq)%s(q%sr)' % (CON, CON, CON, CON, CON, CON))

    def test_analyze_wildly_invalid(self):
        self.assertRaises(ValueError, Formula, 'pqpppppp')
        self.assertRaises(ValueError, Formula, '()()()()p')
        self.assertRaises(ValueError, Formula, '%s%s%s()()%sp' % (NEG, NEG, NEG, NEG))
        self.assertRaises(ValueError, Formula, '%p')
        self.assertRaises(ValueError, Formula, 'q%p')
        self.assertRaises(ValueError, Formula, 'q!@#$p)))')
        self.assertRaises(ValueError, Formula, '%s%s%sq' % (NEG, NEG, CON))
        self.assertRaises(ValueError, Formula, '()')
        self.assertRaises(ValueError, Formula, '(@%s@)' % CON)
        self.assertRaises(ValueError, Formula, '(1%s2)' % CON)

    def test_variables(self):
        self.assertEqual(Formula('%sp' % NEG).variables, ['p'])
        self.assertEqual(Formula('p%sq' % IMP).variables, ['p','q'])
        self.assertEqual(Formula('(q%sr)%s(p%sr)' % (IMP, IMP, IMP)).variables, ['p','q', 'r'])
        self.assertEqual(Formula('((q%sq)%s(p%sp))%s(t%st)' % (IMP, IMP, IMP, IMP, IMP)).variables, ['p','q', 't'])

    def test_assign_simple(self):
       self.assertTrue(Formula('p').assign({'p':True}))
       self.assertFalse(Formula('p').assign({'p':False}))
       self.assertTrue(Formula('%sp' % NEG).assign({'p':False}))
       self.assertFalse(Formula('%sp' % NEG).assign({'p':True}))

    def test_assign_complex1(self):
       f = Formula('q%s(p%sq)' % (IMP, IMP))
       self.assertTrue(f.assign({
           'p' : True,
           'q' : True,
       }))
       self.assertTrue(f.assign({
           'p' : True,
           'q' : False,
       }))
       self.assertTrue(f.assign({
           'p' : False,
           'q' : True,
       }))
       self.assertTrue(f.assign({
           'p' : False,
           'q' : False,
       }))
       self.assertEquals(f.correct_option, Tautology)
       self.assertTrue(f.is_tautology)

    def test_assign_complex2(self):
       f = Formula('(p%s%sp)%s(r%s(q%sr))' % (CON, NEG, CON, IMP, EQV))
       self.assertFalse(f.assign({
           'p' : True,
           'q' : True,
           'r' : True,
       }))
       self.assertFalse(f.assign({
           'p' : True,
           'q' : True,
           'r' : False,
       }))
       self.assertFalse(f.assign({
           'p' : True,
           'q' : False,
           'r' : True,
       }))
       self.assertFalse(f.assign({
           'p' : True,
           'q' : False,
           'r' : False,
       }))
       self.assertFalse(f.assign({
           'p' : False,
           'q' : True,
           'r' : True,
       }))
       self.assertFalse(f.assign({
           'p' : False,
           'q' : True,
           'r' : False,
       }))
       self.assertFalse(f.assign({
           'p' : False,
           'q' : False,
           'r' : True,
       }))
       self.assertFalse(f.assign({
           'p' : False,
           'q' : False,
           'r' : False,
       }))
       self.assertEquals(f.correct_option, Contradiction)
       self.assertTrue(f.is_contradiction)

    def test_assign_complex3(self):
       f = Formula('(p%sq)%s(q%sr)' % (DIS, EQV, DIS))
       self.assertTrue(f.assign({
           'p' : True,
           'q' : True,
           'r' : True,
       }))
       self.assertTrue(f.assign({
           'p' : True,
           'q' : True,
           'r' : False,
       }))
       self.assertTrue(f.assign({
           'p' : True,
           'q' : False,
           'r' : True,
       }))
       self.assertFalse(f.assign({
           'p' : True,
           'q' : False,
           'r' : False,
       }))
       self.assertTrue(f.assign({
           'p' : False,
           'q' : True,
           'r' : True,
       }))
       self.assertTrue(f.assign({
           'p' : False,
           'q' : True,
           'r' : False,
       }))
       self.assertFalse(f.assign({
           'p' : False,
           'q' : False,
           'r' : True,
       }))
       self.assertTrue(f.assign({
           'p' : False,
           'q' : False,
           'r' : False,
       }))
       self.assertEquals(f.correct_option, Contingency)

    def test_equal(self):
       self.assertEqual(
           Formula('%sp' % NEG),
           Formula('%sp' % NEG),
       )
       self.assertEqual(
           Formula('%s(p%sq)' % (NEG, EQV)),
           Formula('%s(p%sq)' % (NEG, EQV)),
       )
       self.assertEqual(
           Formula('%s(p%sq)' % (NEG, EQV)),
           Formula('%s(q%sp)' % (NEG, EQV)),
       )
       self.assertEqual(
           Formula('%s(p%sq)%s(r%sq)' % (NEG, EQV, CON, DIS)),
           Formula('(q%sr)%s%s(q%sp)' % (DIS, CON, NEG, EQV)),
       )

    def test_not_equal(self):
       self.assertNotEqual(
           Formula('%sp' % NEG),
           Formula('p'),
       )
       self.assertNotEqual(
           Formula('%sp' % NEG),
           Formula('%sq' % NEG),
       )
       self.assertNotEqual(
           Formula('%s(p%sq)' % (NEG, EQV)),
           Formula('(p%sq)' % EQV),
       )
       self.assertNotEqual(
           Formula('%s(p%sq)' % (NEG, CON)),
           Formula('%s(q%sp)' % (NEG, DIS)),
       )
       self.assertNotEqual(
           Formula('%s(p%sq)' % (NEG, IMP)),
           Formula('%s(q%sp)' % (NEG, IMP)),
       )
       self.assertNotEqual(
           Formula('%s(p%sq)%s(r%sq)' % (NEG, EQV, CON, IMP)),
           Formula('(q%sr)%s%s(q%sp)' % (IMP, CON, NEG, EQV)),
       )

class PredicateFormulaTests(TestCase):

    def __form(self, s):
        return s.replace('@', ALL) \
                .replace('#', EXS) \
                .replace('-', CON) \
                .replace('>', IMP)

    def _form(self, s):
        return PredicateFormula(
            self.__form(s)
        )

    def test_create(self):
        f = self._form('@xPx')
        self.assertEquals(ALL, f.quantifier)
        self.assertEquals('x', f.quantified)
        self.assertEquals('Px', f.sf1.literal)
        self.assertEquals(self._form('Px'), f.sf1)

    def test_create2(self):
        f = self._form('@x~#yPxy')
        self.assertEquals(ALL, f.quantifier)
        self.assertEquals('x', f.quantified)
        self.assertEquals(self._form('~#yPxy'), f.sf1)
        self.assertEquals(NEG, f.sf1.con)
        self.assertEquals(self._form('#yPxy'), f.sf1.sf1)
        self.assertEquals(EXS, f.sf1.sf1.quantifier)
        self.assertEquals('y', f.sf1.sf1.quantified)
        self.assertEquals(self._form('Pxy'), f.sf1.sf1.sf1)

    def test_create_propositional(self):
        f = self._form('@xPx>#yRay')
        self.assertEquals(IMP, f.con)
        self.assertEquals(None, f.quantifier)
        self.assertEquals(None, f.quantified)
        self.assertEquals(self._form('@xPx'), f.sf1)
        self.assertEquals(self._form('#yRay'), f.sf2)

    def test_create_propositional2(self):
        f = self._form('@xPx>(#yRay-~@x~Px)')
        self.assertEquals(IMP, f.con)
        self.assertEquals(None, f.quantifier)
        self.assertEquals(None, f.quantified)
        self.assertEquals(self._form('@xPx'), f.sf1)
        self.assertEquals(self._form('#yRay-~@x~Px'), f.sf2)
        self.assertEquals(ALL, f.sf1.quantifier)
        self.assertEquals('x', f.sf1.quantified)
        self.assertEquals(self._form('Px'), f.sf1.sf1)
        self.assertEquals(None, f.sf2.quantifier)
        self.assertEquals(None, f.sf2.quantified)
        self.assertEquals(self._form('#yRay'), f.sf2.sf1)
        self.assertEquals(self._form('~@x~Px'), f.sf2.sf2)

    def test_create_with_brackets(self):
        f = self._form('@x(Px>(#yRxy))')
        self.assertEquals(ALL, f.quantifier)
        self.assertEquals('x', f.quantified)
        self.assertEquals(self._form('Px>#yRxy'), f.sf1)
        self.assertEquals(IMP, f.sf1.con)
        self.assertEquals(None, f.sf1.quantifier)
        self.assertEquals(None, f.sf1.quantified)
        self.assertEquals(self._form('Px'), f.sf1.sf1)
        self.assertEquals(self._form('#yRxy'), f.sf1.sf2)

    def test_range(self):
       f = self._form('@xPx') # dummy
       self.assertEquals(self.__form('Px'), quantifier_range(self.__form('@xPx')))
       self.assertEquals(self.__form('@xPx'), quantifier_range(self.__form('@y@xPx')))
       self.assertEquals(self.__form('~Px'), quantifier_range(self.__form('@x~Px')))
       self.assertEquals(self.__form('~@y~Px'), quantifier_range(self.__form('@x~@y~Px')))
       self.assertEquals(self.__form('#xPxy'), quantifier_range(self.__form('@y#xPxy>#y#xPxy')))
       self.assertEquals(self.__form('#x(Pxy>#y#xPxy)'), quantifier_range(self.__form('@y#x(Pxy>#y#xPxy)')))
       self.assertEquals(self.__form('(#xPxy>#y#xPxy)'), quantifier_range(self.__form('@y(#xPxy>#y#xPxy)')))
       self.assertEquals(self.__form('Px'), quantifier_range(self.__form('@xPx>Pa')))

    def test_valid(self):
        self.assertIsNotNone(self._form('@x@y@zRxyz'))
        self.assertIsNotNone(self._form('@x(@y@zRxyz)'))
        self.assertIsNotNone(self._form('~@x~#y~Rxy'))
        self.assertIsNotNone(self._form('@x(#yRxy)'))
        self.assertIsNotNone(self._form('@x(Fx>#yRxy)'))
        self.assertIsNotNone(self._form('(@xFx>#yFy)'))
        self.assertIsNotNone(self._form('(@xFx>#yFy)-Fa'))
        self.assertIsNotNone(self._form('(@xFx>#yFy)>~@x~#y~Rxy'))
        self.assertIsNotNone(self._form('Rxyzxyzxyzxyz'))
        self.assertIsNotNone(self._form('Ra>Rb'))
        self.assertIsNotNone(self._form('~Pa>(~Qb>~Pa)'))
        self.assertIsNotNone(self._form('~~@x~~#yRxy>@x((Sx>#zRxz)-~#w(Rww))'))

    def test_invalid(self):
        self.assertRaises(ValueError, self._form, '@x')
        self.assertRaises(ValueError, self._form, 'x')
        self.assertRaises(ValueError, self._form, '')
        self.assertRaises(ValueError, self._form, '@')
        self.assertRaises(ValueError, self._form, '@x@y')
        self.assertRaises(ValueError, self._form, '~')
        self.assertRaises(ValueError, self._form, '~@x')
        self.assertRaises(ValueError, self._form, 'x@')
        self.assertRaises(ValueError, self._form, '@Fx')
        self.assertRaises(ValueError, self._form, '@xx')
        self.assertRaises(ValueError, self._form, '###')
        self.assertRaises(ValueError, self._form, '@@x')

    def test_invalid2(self):
        self.assertRaises(ValueError, self._form, 'Fx@x')
        self.assertRaises(ValueError, self._form, 'xF')
        self.assertRaises(ValueError, self._form, 'FF')
        self.assertRaises(ValueError, self._form, 'FX')
        self.assertRaises(ValueError, self._form, '@xFX')
        self.assertRaises(ValueError, self._form, '@@xFx')
        self.assertRaises(ValueError, self._form, '@xFx@y')
        self.assertRaises(ValueError, self._form, 'Fx#yFy')
        self.assertRaises(ValueError, self._form, 'F>Fx')
        self.assertRaises(ValueError, self._form, 'Rxy>@Rxyz')
        self.assertRaises(ValueError, self._form, '((@xFx)')
        self.assertRaises(ValueError, self._form, '@xFx~x')
        self.assertRaises(ValueError, self._form, '@xFxFy')
        self.assertRaises(ValueError, self._form, '@x#y@Fxy')

    def test_equal(self):
        self.assertTrue(self._form('@xFx') == self._form('@xFx'))
        self.assertTrue(self._form('@xFxx') == self._form('@xFxx'))
        self.assertTrue(self._form('Ra') == self._form('Ra'))
        self.assertTrue(self._form('@xFx-@xGx') == self._form('@xGx-@xFx'))
        self.assertTrue(self._form('@xFx-@xGx') == self._form('@yGy-@xFx'))
        self.assertTrue(self._form('@yFy') == self._form('@xFx'))
        self.assertTrue(self._form('@yFyy') == self._form('@xFxx'))
        self.assertTrue(self._form('@y@xRyx') == self._form('@x@yRxy'))
        self.assertTrue(self._form('@y@xRyx') == self._form('@u@vRuv'))
        self.assertTrue(self._form('@y@xRyx>#yLyy') == self._form('@u@vRuv>#xLxx'))
        self.assertTrue(self._form('@x#yLxy>#xFx') == self._form('@w#zLwz>#yFy'))
        self.assertTrue(self._form('@x#yLxy-#xFx') == self._form('#yFy-@w#zLwz'))

    def test_not_equal(self):
        self.assertFalse(self._form('@xFx') == self._form('@xFy'))
        self.assertFalse(self._form('@xFx') == self._form('#xFx'))
        self.assertFalse(self._form('Ra') == self._form('Rb'))
        self.assertFalse(self._form('@xRax') == self._form('@xRbx'))
        self.assertFalse(self._form('@xRxx') == self._form('@xRyx'))
        self.assertFalse(self._form('Rx') == self._form('Ry'))
        self.assertFalse(self._form('Rx') == self._form('#xRx'))
        self.assertFalse(self._form('Rxy') == self._form('Ryx'))
        self.assertFalse(self._form('@xFx-@xGy') == self._form('@xGx-@xFx'))
        self.assertFalse(self._form('@xFx-@xGx') == self._form('@yGx-@xFx'))
        self.assertFalse(self._form('@yFy') == self._form('@xFy'))
        self.assertFalse(self._form('@y@xRyx') == self._form('@x#yRxy'))
        self.assertFalse(self._form('#y#xRyx') == self._form('@u@vRuv'))
        self.assertFalse(self._form('@x#yLxy>#xFx') == self._form('@w#zLwz-#yFy'))
        self.assertFalse(self._form('@x#yLxy-#xFx') == self._form('@w#zLxz-#xFx'))

    def test_assign_atomic(self):
        self.assertTrue(self._form('Pa').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'a': 2,
        }))
        self.assertTrue(self._form('Rab').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3)},
            'a': 1,
            'b': 2,
        }))
        self.assertTrue(self._form('Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 1,
            'b': 2,
            'c': 3,
        }))
        self.assertTrue(self._form('Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 2,
            'b': 2,
            'c': 2,
        }))

        self.assertFalse(self._form('Pa').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'a': 1,
        }))
        self.assertFalse(self._form('Rab').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3)},
            'a': 2,
            'b': 2,
        }))
        self.assertFalse(self._form('Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 3,
            'b': 2,
            'c': 3,
        }))

        self.assertFalse(self._form('Pa').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'a': 4,
        }))
        self.assertFalse(self._form('Rab').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3)},
            'a': 7,
            'b': 2,
        }))
        self.assertFalse(self._form('Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 9,
            'b': 2,
            'c': 3,
        }))

        self.assertRaises(KeyError, self._form('Rabc').assign, {
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 9,
            'c': 3,
        })

    def test_assign_propositional(self):
        self.assertTrue(self._form('Pa-Qb').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'Q': {1, 3},
            'a': 2,
            'b': 1,
        }))
        self.assertTrue(self._form('Rab - Rba').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3), (2,1)},
            'a': 2,
            'b': 1,
        }))
        self.assertTrue(self._form('(Rab-Rbc)>Rac').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3)},
            'a': 1,
            'b': 2,
            'c': 3,
        }))
        self.assertTrue(self._form('~~~Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 3,
            'b': 2,
            'c': 1,
        }))
        self.assertTrue(self._form('(Rabc>~Pa)-(~Pa>Rabc)').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'P': {1, 3},
            'a': 2,
            'b': 2,
            'c': 2,
        }))

        self.assertFalse(self._form('Pa-Qb').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'Q': {1, 3},
            'a': 2,
            'b': 2,
        }))
        self.assertFalse(self._form('Rab - Rba').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,3), (2,1)},
            'a': 1,
            'b': 3,
        }))
        self.assertFalse(self._form('(Rab-Rbc)>Rac').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (1,1)},
            'a': 1,
            'b': 2,
            'c': 3,
        }))
        self.assertFalse(self._form('~~~Rabc').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'a': 2,
            'b': 2,
            'c': 2,
        }))
        self.assertFalse(self._form('(Rabc>~Pa)-(~Pa>Rabc)').assign({
            'domain': {1, 2, 3},
            'R': {(1,1,1), (2,2,2), (3,3,3), (1,2,3)},
            'P': {2, 3},
            'a': 2,
            'b': 2,
            'c': 2,
        }))

    def test_assign_simple_quantified(self):
        self.assertTrue(self._form('@xPx').assign({
            'domain': {1, 2, 3},
            'P': {1, 2, 3},
        }))
        self.assertTrue(self._form('@xPx').assign({
            'domain': {},
            'P': {},
        }))
        self.assertTrue(self._form('#xPx').assign({
            'domain': {1, 2, 3},
            'P': {2},
        }))
        self.assertTrue(self._form('@x@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (1,2), (2,1), (2,2), (1,3), (2,3), (3,1), (3,2), (3,3)},
        }))
        self.assertTrue(self._form('@x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (2,2), (2,3), (3,1), (3,2)},
        }))
        self.assertTrue(self._form('#x@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (1,2), (2,3), (1,3)},
        }))
        self.assertTrue(self._form('#x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(3,1)},
        }))
        self.assertTrue(self._form('#x#y#zRxyz').assign({
            'domain': {1, 2, 3},
            'R': {(3,1,2)},
        }))

        self.assertFalse(self._form('@xPx').assign({
            'domain': {1, 2, 3},
            'P': {1, 2},
        }))
        self.assertFalse(self._form('@xPx').assign({
            'domain': {1, 2, 3},
            'P': {},
        }))
        self.assertFalse(self._form('#xPx').assign({
            'domain': {1, 2, 3},
            'P': {},
        }))
        self.assertFalse(self._form('#xPx').assign({
            'domain': {1, 2, 3},
            'P': {4},
        }))
        self.assertFalse(self._form('@x@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(2,1), (2,2), (1,3), (2,3), (3,1), (3,2), (3,3)},
        }))
        self.assertFalse(self._form('@x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (3,1), (3,2)},
        }))
        self.assertFalse(self._form('#x@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (2,3), (1,3)},
        }))
        self.assertFalse(self._form('#x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {},
        }))
        self.assertFalse(self._form('#x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(2,5)},
        }))

    def test_assign_complex_quantified(self):
        self.assertTrue(self._form('@x(Px>Sx)').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'S': {1, 2, 3},
        }))
        self.assertTrue(self._form('@x(Px>Sx)').assign({
            'domain': {1, 2, 3},
            'P': {},
            'S': {3},
        }))
        self.assertTrue(self._form('@x(Px>#y(Sy-Ryx))').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'S': {1, 2},
            'R': {(1,1),(1,2),(1,3),(2,2),(2,3),(3,3)},
        }))
        self.assertTrue(self._form('#x(Px-@y(Rxy))').assign({
            'domain': {1, 2, 3},
            'P': {2},
            'R': {(2,1),(2,3),(2,2)},
        }))
        self.assertTrue(self._form('@x@y((Rxy>Ryx)-(Ryx>Rxy))').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,1), (2,2), (1,3), (2,3), (3,1), (3,2)},
        }))
        self.assertTrue(self._form('@x@y@z((Rxy-Ryz)>Rxz)').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,2), (1,3), (2,3)},
        }))
        self.assertTrue(self._form('~@x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(2,2), (2,3), (3,1), (3,2)},
        }))
        self.assertTrue(self._form('#x~@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (1,2), (2,3), (1,3)},
        }))
        self.assertTrue(self._form('#x#y(Rxy-Ryx)').assign({
            'domain': {1, 2, 3},
            'R': {(3,1), (1,2), (2,1)},
        }))

        self.assertFalse(self._form('@x(Px>Sx)').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'S': {3},
        }))
        self.assertFalse(self._form('@x(Px>#y(Sy-Ryx))').assign({
            'domain': {1, 2, 3},
            'P': {2, 3},
            'S': {1},
            'R': {(1,1),(1,3),(2,2),(2,3),(3,3)},
        }))
        self.assertFalse(self._form('#x(Px-@y(Rxy))').assign({
            'domain': {1, 2, 3},
            'P': {2},
            'R': {(2,1),(2,3)},
        }))
        self.assertFalse(self._form('@x@y((Rxy>Ryx)-(Ryx>Rxy))').assign({
            'domain': {1, 2, 3},
            'R': {(2,1), (2,2), (1,3), (2,3), (3,1), (3,2)},
        }))
        self.assertFalse(self._form('@x@y@z((Rxy-Ryz)>Rxz)').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,2), (2,3)},
        }))
        self.assertFalse(self._form('~@x#yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,2), (2,3), (3,1), (3,2)},
        }))
        self.assertFalse(self._form('#x~@yRxy').assign({
            'domain': {1, 2, 3},
            'R': {(1,1), (1,2), (2,3), (1,3), (2,2), (2,1), (3,3), (3,1), (3,2)},
        }))
        self.assertFalse(self._form('#x#y(Rxy-Ryx)').assign({
            'domain': {1, 2, 3},
            'R': {(3,1), (1,2)},
        }))
        self.assertFalse(self._form('#x#y(Rxy-Ryx)').assign({
            'domain': {1, 2, 3},
            'R': {},
        }))

    def test_predicates(self):
        self.assertEquals({'P'}, set(self._form('Pa').predicates))
        self.assertEquals({'P'}, set(self._form('@xPx').predicates))
        self.assertEquals({'P'}, set(self._form('~@xPx').predicates))
        self.assertEquals({'P'}, set(self._form('@x~(~Px-Px)').predicates))
        self.assertEquals({'P','Q','R'}, set(self._form('((Pa-Qb)>Rab)').predicates))
        self.assertEquals({'P','Q','R'}, set(self._form('@x((Px-Qx)>~#yRxy)').predicates))

    def test_constants(self):
        self.assertEquals({'a'}, set(self._form('Pa').constants))
        self.assertEquals({'a'}, set(self._form('~(Pa-~Pa)').constants))
        self.assertEquals(set(), set(self._form('@xPx').constants))
        self.assertEquals(set(), set(self._form('~@xPx').constants))
        self.assertEquals({'a','b'}, set(self._form('((Pa-Qb)>Rab)').constants))
        self.assertEquals({'a','b','c'}, set(self._form('@x((Rbx-Sxc)>~#yRxa)').constants))

class TruthTableTests(TestCase):

    def test_values1(self):
        tt = TruthTable(Formula('p'))
        self.assertEquals(tt.values, [[True], [False]])

    def test_values2(self):
        tt = TruthTable(Formula('p%sq' % IMP))
        self.assertEquals(tt.values, [[True,  True],
                                      [True,  False],
                                      [False, True],
                                      [False, False]])

    def test_values3(self):
        tt = TruthTable(Formula('(p%sq)%sr' % (IMP, IMP)))
        self.assertEquals(tt.values, [[True,  True,  True],
                                      [True,  True,  False],
                                      [True,  False, True],
                                      [True,  False, False],
                                      [False, True,  True],
                                      [False, True,  False],
                                      [False, False, True],
                                      [False, False, False]])

    def test_result_simple(self):
        tt = TruthTable(Formula('p'))
        self.assertEquals(tt.result, [True, False])

    def test_result_neg(self):
        tt = TruthTable(Formula('%sp' % NEG))
        self.assertEquals(tt.result, [False, True])

    def test_result_con(self):
        tt = TruthTable(Formula('p%sq' % CON))
        self.assertEquals(tt.result, [True,
                                      False,
                                      False,
                                      False])

    def test_result_dis(self):
        tt = TruthTable(Formula('p%sq' % DIS))
        self.assertEquals(tt.result, [True,
                                      True,
                                      True,
                                      False])

    def test_result_eqv(self):
        tt = TruthTable(Formula('p%sq' % EQV))
        self.assertEquals(tt.result, [True,
                                      False,
                                      False,
                                      True])

    def test_result_imp(self):
        tt = TruthTable(Formula('p%sq' % IMP))
        self.assertEquals(tt.result, [True,
                                      False,
                                      True,
                                      True])

    def test_result_complex(self):
        tt = TruthTable(Formula('(p%s%sq)%s(r%sq)' % (CON, NEG, DIS, EQV))) # (p&~q)v(r=q)
        self.assertEquals(tt.result, [True,  # TTT
                                      False, # TTF
                                      True,  # TFT
                                      True,  # TFF
                                      True,  # FTT
                                      False, # FTF
                                      False, # FFT
                                      True]) # FFF

class MultiTruthTableTests(TestCase):

    def test_values1(self):
        tt = MultiTruthTable(FormulaSet('p').formulas)
        self.assertEquals(tt.values, [[True], [False]])

    def test_values2(self):
        tt = MultiTruthTable(FormulaSet('p%sq,%sp,r' % (EQV, NEG)).formulas)
        self.assertEquals(tt.values, [[True,  True,  True],
                                      [True,  True,  False],
                                      [True,  False, True],
                                      [True,  False, False],
                                      [False, True,  True],
                                      [False, True,  False],
                                      [False, False, True],
                                      [False, False, False]])

    def test_result_simple(self):
        tt = MultiTruthTable(FormulaSet('p%sq,p%sq,p%sq,p%sq' % (CON, DIS, EQV, IMP)).formulas)
        self.assertEquals(tt.result,[
            [True,
             False,
             False,
             False],
            [True,
             True,
             True,
             False],
            [True,
             False,
             False,
             True],
            [True,
             False,
             True,
             True],
        ])

class FormulaSetTests(TestCase):

    def test_create(self):
        self.assertEquals(FormulaSet('p,q,r,s').formulas, [Formula('p'), Formula('q'), Formula('r'), Formula('s')])
        self.assertEquals(FormulaSet('p, q, r,s').formulas, [Formula('p'), Formula('q'), Formula('r'), Formula('s')])
        self.assertEquals(FormulaSet('p,p,q,q').formulas, [Formula('p'), Formula('q')])
        self.assertEquals(FormulaSet('p,p%sq' % CON).formulas, [Formula('p'), Formula('p%sq' % CON)])

    def test_create_invalid(self):
        self.assertRaises(ValueError, FormulaSet, '')
        self.assertRaises(ValueError, FormulaSet, 'p,,q')
        self.assertRaises(ValueError, FormulaSet, '{p,q}')
        self.assertRaises(ValueError, FormulaSet, 'pqrs')
        self.assertRaises(ValueError, FormulaSet, 'p,q,r%s,' % CON)

    def test_consistent(self):
        self.assertTrue(FormulaSet('p').is_consistent)
        self.assertTrue(FormulaSet('p,q,r').is_consistent)
        self.assertTrue(FormulaSet('p%sq,q%sr' % (CON, IMP)).is_consistent)
        self.assertTrue(FormulaSet('p,p,r').is_consistent)
        self.assertTrue(FormulaSet('p%sq,p%sp,(p%s(q%sr))%sr' % (CON, IMP, IMP, DIS, EQV)).is_consistent)

    def test_inconsistent(self):
        self.assertFalse(FormulaSet('p,%sp' % NEG).is_consistent)
        self.assertFalse(FormulaSet('p,%sp,q,r,s' % NEG).is_consistent)
        self.assertFalse(FormulaSet('p%sq,p%sq,%sp%sq' % (CON, DIS, NEG, EQV)).is_consistent)

class ArgumentTests(TestCase):

    def test_create(self):
        arg = Argument(u'∴p')
        self.assertEquals(arg.premises, [])
        self.assertEquals(arg.conclusion, Formula('p'))
        arg = Argument(u'p,q∴r')
        self.assertEquals(arg.premises, FormulaSet('p,q'))
        self.assertEquals(arg.conclusion, Formula('r'))
        prem = 'p%sr,%sq,(r%sq)%sp' % (CON, NEG, DIS, EQV)
        conc = '(p%sr)%sq' % (CON, IMP)
        arg = Argument(u'%s∴%s' % (prem, conc))
        self.assertEquals(arg.premises, FormulaSet(prem))
        self.assertEquals(arg.conclusion, Formula(conc))

    def test_create_invalid(self):
        self.assertRaises(ValueError, Argument, 'p')
        self.assertRaises(ValueError, Argument, 'p,q,r')
        self.assertRaises(ValueError, Argument, u'p,q,r∴')

    def test_valid_argument(self):
        self.assertTrue(Argument(u'∴(p%s%sp)' % (DIS, NEG)).is_valid)
        self.assertTrue(Argument(u'p,p%sq∴q' % IMP).is_valid)
        self.assertTrue(Argument(u'p%sq,q%sr∴p%sr' % (IMP, IMP, IMP)).is_valid)
        self.assertTrue(Argument(u'p%sq,q%sp∴p%sq' % (IMP, IMP, EQV)).is_valid)
        self.assertTrue(Argument(u'p,%sp∴(p%sp)' % (NEG, CON)).is_valid)

    def test_invalid_argument(self):
        self.assertFalse(Argument(u'∴(p%sp)' % DIS).is_valid)
        self.assertFalse(Argument(u'p,q,r,s,t,u,v∴(p%sx)' % CON).is_valid)
        self.assertFalse(Argument(u'p,q,p∴(p%s%sp)' % (CON, NEG)).is_valid)
