import json

from datetime import datetime, timedelta
from itertools import groupby

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase

from .formula import (
    Formula,
    TruthTable,
    NEG,
    CON,
    DIS,
    IMP,
    EQV,
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
    DeductionQuestion,
    UserAnswer,
    UserChapter,
)

def login(self):
    u = User.objects.create_superuser('u', 'u@hi.com', 'pw')
    self.user = u
    self.client.login(username = 'u', password = 'pw')

class IndexViewTests(TestCase):

    def setUp(self):
        login(self)

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
        response = self.client.get(reverse('logic:index'))
        self._assertHas(response, chapters)
 
    def test_index_many_chapters(self):
        chapters = [Chapter.objects.create(title='chapternum%s'%i, number=i) for i in range(1,6)]
        response = self.client.get(reverse('logic:index'))
        self._assertHas(response, chapters)

class QuestionViewTests(TestCase):
 
    def setUp(self):
        self.chapter = Chapter.objects.create(title='chap', number=1)
        login(self)

    def _create_choice_question(self, num_choices=1):
        q = ChoiceQuestion.objects.create(chapter=self.chapter, number=1, text='hithere')
        choices = []
        for i in range(num_choices):
            choices.append(Choice.objects.create(question=q, text='choicenum%s'%i, is_correct=(i==1)))
        return q, choices

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

    def _post_choice(self, question, choice):
        response = self.client.post(self._get_url(question), {'choice':choice.id})
        self._assertJSON(response, {'correct':choice.is_correct})

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
        self.assertEquals(len(UserChapter.objects.filter(chapter=self.chapter,user=self.user)), 1)

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
        qc = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        qo = OpenQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        qf = FormulationQuestion.objects.create(chapter=chapter, text='hi?', number=3)
        qt = TruthTableQuestion.objects.create(chapter=chapter, formula='pvq', number=4)
        qd = DeductionQuestion.objects.create(chapter=chapter, formula='pvq', number=5)
        self.assertItemsEqual(Question._all(), [qc, qo, qf, qt, qd])
        self.assertItemsEqual(Question._filter(chapter=chapter), [qc, qo, qf, qt, qd])
        self.assertItemsEqual(Question._filter(number=5), [qd])
        self.assertEqual(Question._get(number=5), qd)
        self.assertEqual(Question._count(), 5)

class UserChapterTests(TestCase):

    def test_percent_correct(self):
        user = User.objects.create(username='u', password='pw')
        chapter = Chapter.objects.create(title='chap', number=1)
        # with 1 question
        q = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=1)
        uc = UserChapter.objects.create(chapter=chapter,user=user)
        ua = UserAnswer.objects.create(chapter=chapter,user=user,user_chapter=uc, question_number=q.number,correct=False)
        self.assertEquals(uc.percent_correct(), 0)
        ua.correct = True
        ua.save()
        self.assertEquals(uc.percent_correct(), 100)
        # 2nd question
        q2 = ChoiceQuestion.objects.create(chapter=chapter, text='hi?', number=2)
        ua2 = UserAnswer.objects.create(chapter=chapter,user=user,user_chapter=uc, question_number=q2.number,correct=False)
        self.assertEquals(uc.percent_correct(), 50)
        ua2.correct = True
        ua2.save()
        self.assertEquals(uc.percent_correct(), 100)

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

    def test_analyze_invalid(self):
        self.assertRaises(ValueError, Formula, 'pq')
        self.assertRaises(ValueError, Formula, '%sp' % IMP)
        self.assertRaises(ValueError, Formula, 'p%s' % IMP)
        self.assertRaises(ValueError, Formula, '((p%sq)' % CON)
        self.assertRaises(ValueError, Formula, '(p%sq))' % CON)
        self.assertRaises(ValueError, Formula, '(p%sq))' % CON)
        self.assertRaises(ValueError, Formula, '(p%sq%sr)' % (CON, CON))
        self.assertRaises(ValueError, Formula, '%s%s%s%sq' % (CON, DIS, IMP, EQV))
        self.assertRaises(ValueError, Formula, '(p%s%s%s%sq)' % (CON, DIS, IMP, EQV))

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
        self.assertEqual(Formula('%sp' % NEG).variables(), ['p'])
        self.assertEqual(Formula('p%sq' % IMP).variables(), ['p','q'])
        self.assertEqual(Formula('(q%sr)%s(p%sr)' % (IMP, IMP, IMP)).variables(), ['p','q', 'r'])
        self.assertEqual(Formula('((q%sq)%s(p%sp))%s(t%st)' % (IMP, IMP, IMP, IMP, IMP)).variables(), ['p','q', 't'])

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

