
// =============
// imports
// =============

var lib = require('./testslib.js');

var Formula = lib.Formula;
var PredicateFormula = lib.PredicateFormula;
var Argument = lib.Argument;
var Deduction = lib.Deduction;

var quantifierRange = lib.quantifierRange;

var symbols = {
    '~': lib.NEG,
    '-': lib.CON,
    'v': lib.DIS,
    '>': lib.IMP,
    '=': lib.EQV,
    '@': lib.ALL,
    '#': lib.EXS,
    ':': lib.THF,
};

// =============
// tests
// =============

var count = 0;
var error = false;
var t1 = new Date().getTime();

try {

// ===== tests start =====

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ---    formula tests    --- 
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // ----------------
    // creation tests 
    // ----------------

    // valid cases
    assertForm('~p', '~', 'p', '');
    assertForm('P-Q', '-', 'P', 'Q');
    assertForm('~~~p', '~', '~~p', '');
    assertForm('~(~~p)', '~', '~~p', '');
    assertForm('p-q', '-', 'p', 'q');
    assertForm('p-~~q', '-', 'p', '~~q');
    assertForm('(p-q)>~r', '>', 'p-q', '~r');
    assertForm('((~p)-~r)>p', '>', '(~p)-~r', 'p');
    assertForm('~~p=~((p-q)v(qvs))', '=', '~~p', '~((p-q)v(qvs))');

    // more scrutiny
    var sf1_sf1 = '~p';
    var sf1_sf2 = 'q';
    var sf1 = '(' + sf1_sf1 + ')v(' + sf1_sf2 + ')';
    var sf2_sf1 = '~~r';
    var sf2_sf2 = '(p)';
    var sf2 = '(' + sf2_sf1 + ')>(' + sf2_sf2 + ')';
    var f = '(' + sf1 + ')=(' + sf2 + ')';

    var frm = formula(f);
    var frm_sf1 = formula(sf1);
    var frm_sf2 = formula(sf2);
    var frm_sf1_sf1 = formula(sf1_sf1);
    var frm_sf1_sf2 = formula(sf1_sf2);
    var frm_sf2_sf1 = formula(sf2_sf1);
    var frm_sf2_sf2 = formula(sf2_sf2);

    assertEquals(frm.con, form('='));
 
    assertTrue(frm.sf1.equals(frm_sf1));
    assertEquals(frm.sf1.con, form('v'));
    assertTrue(frm.sf1.sf1.equals(frm_sf1_sf1));
    assertEquals(frm.sf1.sf1.con, form('~'));
    assertEquals(frm.sf1.sf1.sf1.con, null);
    assertTrue(frm.sf1.sf2.equals(frm_sf1_sf2));
    assertEquals(frm.sf1.sf2.con, null);

    assertTrue(frm.sf2.equals(frm_sf2));
    assertEquals(frm.sf2.con, form('>'));
    assertTrue(frm.sf2.sf1.equals(frm_sf2_sf1));
    assertEquals(frm.sf2.sf1.con, form('~'));
    assertEquals(frm.sf2.sf1.sf1.con, form('~'));
    assertTrue(frm.sf2.sf2.equals(frm_sf2_sf2));
    assertEquals(frm.sf2.sf2.con, null);

    // invalid cases
    assertInvalidForm('p~');
    assertInvalidForm('~');
    assertInvalidForm('1');
    assertInvalidForm('p~p');
    assertInvalidForm('p-');
    assertInvalidForm('p-q-r');
    assertInvalidForm('((p>q)');
    assertInvalidForm('(p>q))');
    assertInvalidForm('');
    assertInvalidForm('(');
    assertInvalidForm(')');
    assertInvalidForm('()');
    assertInvalidForm('(p-q(-r)');
    assertInvalidForm('(p-q)(-r)');
    assertInvalidForm('(p-q)>(dsadas21)');
    assertInvalidForm('(p-q)>(-r)');
    assertInvalidForm('(2-1)');
    assertInvalidForm('pp');
    assertInvalidForm('p--q');
    assertInvalidForm('(~p>~q)v(p=r');
    assertInvalidForm('(~p>~q)vp=r');
    assertInvalidForm('(~p>~q)vp=r)');
    assertInvalidForm('(~p>~q)v(p=r~)');
    assertInvalidForm('(~p>~q)v(p=r)~');
    assertInvalidForm('(~p>~q)~v(p=r)');

    // ----------------
    // negation tests 
    // ----------------

    assertTrue(formula('~p').isNegationOf(formula('p')));
    assertTrue(formula('~~p').isNegationOf(formula('~p')));
    assertTrue(formula('(~p)').isNegationOf(formula('p')));
    assertTrue(formula('~(~p)').isNegationOf(formula('~p')));
    assertTrue(formula('~(~(~p))').isNegationOf(formula('~~p')));
    assertTrue(formula('(~(~(~p)))').isNegationOf(formula('~~p')));
    assertTrue(formula('~(r-q)').isNegationOf(formula('q-r')));
    assertTrue(formula('(~(r-q))').isNegationOf(formula('q-r')));
    assertTrue(formula('~(r-q)').isNegationOf(formula('(r-q)')));
    assertTrue(formula('~(r-q)').isNegationOf(formula('r-q')));
    assertTrue(formula('~((r-q)v(p=q))').isNegationOf(formula('(q=p)v(q-r)')));

    assertFalse(formula('~((r-q)v(p=q))').isNegationOf(formula('(q=p)-(q-r)')));
    assertFalse(formula('~(r>q)').isNegationOf(formula('q>r')));
    assertFalse(formula('~~p').isNegationOf(formula('p')));
    assertFalse(formula('~q').isNegationOf(formula('p')));
    assertFalse(formula('~qvp').isNegationOf(formula('qvp')));

    // ----------------
    // contradiction tests 
    // ----------------

    assertTrue(formula('p-~p').isContradiction());
    assertTrue(formula('~p-p').isContradiction());
    assertTrue(formula('~~p-~p').isContradiction());
    assertTrue(formula('~~p-~~~p').isContradiction());
    assertTrue(formula('~(~(p))-~(~~p)').isContradiction());
    assertTrue(formula('~(p>q)-(p>q)').isContradiction());
    assertTrue(formula('(p>q)-~(p>q)').isContradiction());
    assertTrue(formula('(p=q)-~(q=p)').isContradiction());

    assertFalse(formula('p-p').isContradiction());
    assertFalse(formula('~p-~p').isContradiction());
    assertFalse(formula('~pvp').isContradiction());
    assertFalse(formula('~p>p').isContradiction());
    assertFalse(formula('(p>q)-(~p>q)').isContradiction());

    // ----------------
    // equals tests 
    // ----------------

    assertTrue(formula('p').equals(formula('p')));
    assertTrue(formula('pvr').equals(formula('pvr')));
    assertTrue(formula('pvr').equals(formula('rvp')));
    assertTrue(formula('(pvr)').equals(formula('rvp')));
    assertTrue(formula('(pvr)').equals(formula('(rvp)')));
    assertTrue(formula('~(pvr)').equals(formula('~(rvp)')));
    assertTrue(formula('~(pv~r)').equals(formula('~(~rvp)')));
    assertTrue(formula('(pvr)v(qvs)').equals(formula('((svq)v(rvp))')));

    assertFalse(formula('p').equals(formula('q')));
    assertFalse(formula('~p').equals(formula('~q')));
    assertFalse(formula('p>r').equals(formula('r>p')));
    assertFalse(formula('(pvq)-r').equals(formula('pv(q-r)')));
    assertFalse(formula('(p-r)=(qvs)').equals(formula('((s-q)=(rvp))')));
    assertFalse(formula('~(pvr)').equals(formula('~rvp')));
    assertFalse(formula('~pvr').equals(formula('~rvp')));
    assertFalse(formula('~pvr').equals(formula('~(pvr)')));

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ---   predicate formula tests   --- 
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // ----------------------
    // quantifier range tests 
    // ----------------------

    assertEquals(form('Px'), quantifierRange(form('@xPx')));
    assertEquals(form('Px'), quantifierRange(form('#xPx')));
    assertEquals(form('@yRxy'), quantifierRange(form('@x@yRxy')));
    assertEquals(form('~@yRxy'), quantifierRange(form('#x~@yRxy')));
    assertEquals(form('~@y~Rxy'), quantifierRange(form('@x~@y~Rxy')));
    assertEquals(form('~Rxy'), quantifierRange(form('@x~Rxy')));
    assertEquals(form('Px'), quantifierRange(form('@xPx>Pa')));
    assertEquals(form('~~Px'), quantifierRange(form('@x~~Px>Pa')));
    assertEquals(form('(Px>#yMy)'), quantifierRange(form('@x(Px>#yMy)>Pa')));

    assertUndefined(quantifierRange(form('@x')));
    assertUndefined(quantifierRange(form('@')));

    // ----------------
    // creation tests 
    // ----------------

    assertPredicateForm('Pa', '', '', '', '', '');
    assertPredicateForm('~Pa', '~', 'Pa', '', '', '');
    assertPredicateForm('Rxy>Ryx', '>', 'Rxy', 'Ryx', '', '');
    assertPredicateForm('Rxy>~Sxyz', '>', 'Rxy', '~Sxyz', '', '');
    assertPredicateForm('((Rxy)>Ryx)', '>', 'Rxy', 'Ryx', '', '');

    assertPredicateForm('@xPx', '', 'Px', '', '@', 'x');
    assertPredicateForm('@x~Px', '', '~Px', '', '@', 'x');
    assertPredicateForm('@x#yLxy', '', '#yLxy', '', '@', 'x');
    assertPredicateForm('#y@xLxy', '', '@xLxy', '', '#', 'y');
    assertPredicateForm('@x(#yLxy>Mx)', '', '#yLxy>Mx', '', '@', 'x');
    assertPredicateForm('@x#y@z@wUxyzw', '', '#y@z@wUxyzw', '', '@', 'x');

    assertPredicateForm('~@xPx', '~', '@xPx', '', '', '');
    assertPredicateForm('@xPx>(@yLy>@xPx)', '>', '@xPx', '@yLy>@xPx', '', '');
    assertPredicateForm('@x#yLxy>@xMx', '>', '@x#yLxy', '@xMx', '', '');

    assertInvalidForm('@x', PredicateFormula);
    assertInvalidForm('@', PredicateFormula);
    assertInvalidForm('', PredicateFormula);
    assertInvalidForm('@x#y', PredicateFormula);
    assertInvalidForm('@x#y@z', PredicateFormula);
    assertInvalidForm('@Px', PredicateFormula);
    assertInvalidForm('@xxPx', PredicateFormula);
    assertInvalidForm('@@xPx', PredicateFormula);
    assertInvalidForm('@xP', PredicateFormula);
    assertInvalidForm('aP', PredicateFormula);
    assertInvalidForm('aRb', PredicateFormula);
    assertInvalidForm('#yPy>@x', PredicateFormula);

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ---    argument tests    --- 
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    var a = new Argument(form('p,q:r'));
    assertFormulasEqual(formula('r'), a.conclusion);
    assertListsEqual([formula('p'), formula('q')], a.premises);

    var a = new Argument(form('p,p>q,q>p:p-(p=q)'));
    assertFormulasEqual(formula('p-(p=q)'), a.conclusion);
    assertListsEqual([formula('p'), formula('p>q'), formula('q>p')], a.premises);

    var a = new Argument(form('(p),(p>q),q>p:(pvq)'));
    assertFormulasEqual(formula('pvq'), a.conclusion);
    assertListsEqual([formula('p'), formula('p>q'), formula('q>p')], a.premises);

    var a = new Argument(form(':pv~p'));
    assertFormulasEqual(formula('pv~p'), a.conclusion);
    assertListsEqual([], a.premises);

    assertInvalidArgument(':');
    assertInvalidArgument(',,:');
    assertInvalidArgument('p,q,:p');
    assertInvalidArgument(',:p');
    assertInvalidArgument(',p:p');
    assertInvalidArgument(',p:p:');
    assertInvalidArgument(',p:p:');
    assertInvalidArgument('p:p,q');
    assertInvalidArgument('(q,p:p)');
    assertInvalidArgument('(q,p):p');
    assertInvalidArgument('(,):p');
    assertInvalidArgument('():p');
    assertInvalidArgument('1:p');
    assertInvalidArgument('1:2');
    assertInvalidArgument(':2');
    assertInvalidArgument('p,():p');
    assertInvalidArgument('p:()');
    assertInvalidArgument('(p,q),r:p');

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ---    deduction tests    --- 
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // ----------------
    // impE tests 
    // ----------------

    assertTrue(
        deduction('p', 'p>q').
        impE(1,2).equals(formula('q'))
    );
    assertTrue(
        deduction('p>q', 'p').
        impE(1,2).equals(formula('q'))
    );
    assertTrue(
        deduction('p>q', 'p').
        impE(2,1).equals(formula('q'))
    );
    assertTrue(
        deduction('(p)', 'p>q').
        impE(1,2).equals(formula('q'))
    );
    assertTrue(
        deduction('(p>q)>(r>q)', 'p>q').
        impE(1,2).equals(formula('r>q'))
    );
    assertTrue(
        deduction('(p>q)>(r>q)', '(p>q)').
        impE(1,2).equals(formula('r>q'))
    );
    assertTrue(
        deduction('q-p', '(p-q)>q').
        impE(1,2).equals(formula('q'))
    );
    assertTrue(
        deduction('~((pvq)=(p-~r))>((q>r)=~~p)', '~((qvp)=(~r-p))').
        impE(1,2).equals(formula('(q>r)=~~p'))
    );

    assertUndefined(deduction('p>q','q').impE(1,2));
    assertUndefined(deduction('p>q','p').impE(0,2));
    assertUndefined(deduction('p>q','p').impE(1,3));
    assertUndefined(deduction('p>q','p').impE(2,4));
    assertUndefined(deduction('p>q','~p').impE(1,2));
    assertUndefined(deduction('p>q','p>q').impE(1,2));
    assertUndefined(deduction('(p-q)>q','pvq').impE(1,2));
    assertUndefined(deduction('~(p-q)>q','~p-q').impE(1,2));
    assertUndefined(deduction('(p-q)=q','p-q').impE(1,2));

    // ----------------
    // conE tests 
    // ----------------

    assertListsEqual(
        [formula('q'), formula('p')],
        deduction('q-p').conE(1)
    );

    assertListsEqual(
        [formula('~p'), formula('~q')],
        deduction('~p-~q').conE(1)
    );
    assertListsEqual(
        [formula('~p-~q'), formula('p-r')],
        deduction('((~p-~q)-(p-r))').conE(1)
    );

    assertUndefined(deduction('((~p-~q)>(p-r))').conE(1));
    assertUndefined(deduction('~(p-q)').conE(1));
    assertUndefined(deduction('p').conE(1));
    assertUndefined(deduction('p-q').conE(0));
    assertUndefined(deduction('p-q').conE(2));

    // ----------------
    // disE tests 
    // ----------------

    assertFormulasEqual(
        formula('r'),
        deduction('p>r', 'q>r', 'pvq').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('p>r', 'q>r', 'pvq').disE(2,3,1)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('p>r', 'q>r', 'pvq').disE(3,1,2)
    );
    assertFormulasEqual(
        formula('q'),
        deduction('p>q', 'r>q', 'pvr').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('~~(r)'),
        deduction('(p-q)>(~~r)', '(qvs)>~~(r)', '(svq)v(q-p)').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('q=p'),
        deduction('(~r>(p=q))', '~~~(~svp)>(q=p)', '((~r)v~~~(pv~s))').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('rvs'),
        deduction('(p>(svr))', '~p>(rvs)', 'pv~p').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('rvs'),
        deduction('(p>(svr))', 'p>(rvs)', 'pvp').disE(1,2,3)
    );

    assertUndefined(deduction('(p>(svr))', '~p=(rvs)', 'pv~p').disE(1,2,3));
    assertUndefined(deduction('(p>(svr))', 'p=(rvs)', 'pv~p').disE(1,2,3));
    assertUndefined(deduction('(p>(svr))', 'q=(rvs)', 'pvr').disE(1,2,3));
    assertUndefined(deduction('(p>(svr))', '~p=(r=s)', 'pv~p').disE(1,2,3));
    assertUndefined(deduction('p>q', 'r>q', 'pvr').disE(0,2,3));
    assertUndefined(deduction('p>q', 'r>q', 'pvr').disE(1,2,10));

    // ----------------
    // eqvE tests 
    // ----------------

    assertListsEqual(
        [formula('q>p'), formula('p>q')],
        deduction('q=p').eqvE(1)
    );
    assertListsEqual(
        [formula('(p=q)>~(rv~s)'), formula('~(rv~s)>(p=q)')],
        deduction('(p=q)=~(rv~s)').eqvE(1)
    );

    assertUndefined(deduction('p').eqvE(1));
    assertUndefined(deduction('pvq').eqvE(1));
    assertUndefined(deduction('p>(svr)').eqvE(1));
    assertUndefined(deduction('p=q').eqvE(0));
    assertUndefined(deduction('p=q').eqvE(2));

    // ----------------
    // negE tests 
    // ----------------

    assertFormulasEqual(
        formula('r'),
        deduction('~~r').negE(1)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('(~~r)').negE(1)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('~~(r)').negE(1)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('~(~r)').negE(1)
    );
    assertFormulasEqual(
        formula('~r'),
        deduction('~~~r').negE(1)
    );
    assertFormulasEqual(
        formula('~r'),
        deduction('~~(~r)').negE(1)
    );
    assertFormulasEqual(
        formula('~sv~r'),
        deduction('~~(~sv~r)').negE(1)
    );

    assertUndefined(deduction('p>(svr)').negE(1));
    assertUndefined(deduction('~p').negE(1));
    assertUndefined(deduction('~~s>p').negE(1));
    assertUndefined(deduction('pv~~s').negE(1));
    assertUndefined(deduction('~~s').negE(0));
    assertUndefined(deduction('~~s').negE(2));

    // ----------------
    // conI tests 
    // ----------------

    assertFormulasEqual(
        formula('~~r-p'),
        deduction('~~r', 'p').conI(1,2)
    );
    assertFormulasEqual(
        formula('(p>q)-(~qvr)'),
        deduction('p>q', '~qvr').conI(1,2)
    );
    assertFormulasEqual(
        formula('(r-q)-~p'),
        deduction('r-q', '~p').conI(1,2)
    );

    // ----------------
    // disI tests 
    // ----------------

    assertFormulasEqual(
        formula('~~rvp'),
        deduction('~~r').disI(1,formula('p'))
    );
    assertFormulasEqual(
        formula('(p>q)v(~qvr)'),
        deduction('p>q').disI(1,formula('~qvr'))
    );
    assertFormulasEqual(
        formula('(rvq)v~p'),
        deduction('rvq').disI(1,formula('~p'))
    );

    // ----------------
    // eqvI tests 
    // ----------------

    assertFormulasEqual(
        formula('p=q'),
        deduction('p>q', '((q)>p)').eqvI(1,2)
    );
    assertFormulasEqual(
        formula('p=q'),
        deduction('p>q', '((q)>p)').eqvI(2,1)
    );
    assertFormulasEqual(
        formula('p=(q)'),
        deduction('p>(q)', '((q)>p)').eqvI(1,2)
    );
    assertFormulasEqual(
        formula('~r=p'),
        deduction('~r>p', 'p>~r').eqvI(1,2)
    );
    assertFormulasEqual(
        formula('(q-p)=(s=r)'),
        deduction('(q-p)>(s=r)', '(r=s)>(p-q)').eqvI(1,2)
    );
    assertFormulasEqual(
        formula('((~~rvp)vs)=~(s-p)'),
        deduction('((~~rvp)vs)>~(s-p)', '~(p-s)>(sv(~~rvp))').eqvI(1,2)
    );

    assertUndefined(deduction('p>q', 'p>q').eqvI(1,2));
    assertUndefined(deduction('p>q', 'q>~p').eqvI(1,2));
    assertUndefined(deduction('(p>q)>r', '(r>p)>q').eqvI(1,2));
    assertUndefined(deduction('(q-p)>(s=r)', '(rvs)>(p-q)').eqvI(1,2));
    assertUndefined(deduction('p>q', 'q>p').eqvI(0,2));
    assertUndefined(deduction('p>q', 'q>p').eqvI(2,3));

    // ----------------
    // impI tests 
    // ----------------

    var d = deduction();
    d.hyp(formula('p'));
    assertEquals(1, d.nesting());
    assertEquals(1, d.openIndex());
    assertFormulasEqual(formula('p>p'), d.impI());
    assertUndefined(d.impI());
    assertEquals(0, d.nesting());
    assertUndefined(d.openIndex());
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);

    var d = deduction();
    d.hyp(formula('p'));
    d.hyp(formula('q'));
    assertEquals(2, d.nesting());
    assertEquals(2, d.openIndex());
    assertFormulasEqual(formula('q>q'), d.impI());
    assertEquals(1, d.nesting());
    assertEquals(1, d.openIndex());
    assertFormulasEqual(formula('p>(q>q)'), d.impI());
    assertEquals(0, d.nesting());
    assertUndefined(d.openIndex());
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(2, d.nestingLevels[2]);
    assertEquals(1, d.nestingLevels[3]);
    assertEquals(0, d.nestingLevels[4]);

    assertUndefined(deduction().impI());
    assertUndefined(deduction('p>q').impI());
    assertUndefined(deduction('p>q', 'p').impI());

    // ----------------
    // negI tests 
    // ----------------

    var d = deduction();
    d.hyp(formula('p-~p'));
    assertFormulasEqual(formula('~(p-~p)'), d.negI());
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);

    var d = deduction();
    d.hyp(formula('(~qvp)-~(pv~q)'));
    assertFormulasEqual(formula('~((~qvp)-~(pv~q))'), d.negI());
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);

    assertUndefined(deduction().negI());
    assertUndefined(deduction('p-~p').negI());
    assertUndefined(deduction('p-~p', 'p').negI());
    var d = deduction();
    d.hyp(formula('pv~p'));
    assertUndefined(d.negI());
    var d = deduction();
    d.hyp(formula('~p'));
    assertUndefined(d.negI());


    // ----------------
    // rep tests 
    // ----------------

    var d = deduction('p');
    d.hyp(formula('q'));
    assertFormulasEqual(formula('p'), d.rep(1));
    assertError(d, d.rep, [2], 'הנוכחית');
    assertUndefined(d.rep(5));
    assertUndefined(d.rep(0));

    var d = deduction('p');
    d.hyp(formula('q'));
    d.impI();  // 3. q>q
    assertError(d, d.rep, [1], 'הנוכחית');
    assertError(d, d.rep, [2], 'אחרת');
    d.hyp(formula('q'));
    assertFormulasEqual(formula('p'), d.rep(1));
    assertFormulasEqual(formula('q>q'), d.rep(3));
    assertError(d, d.rep, [2], 'אחרת');
    d.impI(); // 5. q>q
    assertError(d, d.rep, [3], 'הנוכחית');
    assertError(d, d.rep, [4], 'אחרת');

    var d = deduction('p');			// 1. p
    d.hyp(formula('q'));			// 2. | q
    d.rep(1);  					// 3. | p
    assertUndefined(d.rep(5));
    d.hyp(formula('~p'));			// 4. ||~p
    d.rep(1); 					// 5. || p
    d.conI(4,5);				// 6. || ~p-p
    d.negI();					// 7. | ~~p
    assertError(d, d.rep, [2], 'הנוכחית');
    assertError(d, d.rep, [3], 'הנוכחית');
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [5], 'אחרת');
    assertError(d, d.rep, [6], 'אחרת');
    d.hyp(formula('p'));			// 8. || p
    d.rep(2);					// 9. || q
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [5], 'אחרת');
    assertError(d, d.rep, [6], 'אחרת');
    d.impI();					// 10. | p>q
    assertError(d, d.rep, [2], 'הנוכחית');
    assertError(d, d.rep, [3], 'הנוכחית');
    d.hyp(formula('p'));			// 11. || p
    d.hyp(formula('p'));			// 12. ||| p
    d.hyp(formula('p'));			// 13. |||| p
    d.rep(10);					// 14. |||| p>q
    d.rep(11);					// 15. |||| p
    d.rep(12);					// 16. |||| p
    assertError(d, d.rep, [8], 'אחרת');
    d.rep(3);					// 17. |||| p
    assertError(d, d.rep, [14], 'הנוכחית');
    assertError(d, d.rep, [15], 'הנוכחית');
    d.impI();					// 18. ||| p>p
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [8], 'אחרת');
    assertError(d, d.rep, [14], 'אחרת');
    assertError(d, d.rep, [16], 'אחרת');
    d.impI();					// 19. || p>p
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [8], 'אחרת');
    assertError(d, d.rep, [14], 'אחרת');
    assertError(d, d.rep, [16], 'אחרת');
    d.rep(1);					// 20. || p
    d.rep(2);					// 21. || q
    d.rep(7);					// 22. || ~~p
    d.rep(10);					// 23. || p>q
    assertError(d, d.rep, [9], 'אחרת');
    assertError(d, d.rep, [11], 'הנוכחית');
    d.rep(1);					// 24. || p
    d.impI();					// 25. | p>p
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [8], 'אחרת');
    assertError(d, d.rep, [11], 'אחרת');
    assertError(d, d.rep, [12], 'אחרת');
    assertError(d, d.rep, [14], 'אחרת');
    assertError(d, d.rep, [16], 'אחרת');
    assertError(d, d.rep, [18], 'אחרת');
    assertError(d, d.rep, [20], 'אחרת');
    assertError(d, d.rep, [2], 'הנוכחית');
    assertError(d, d.rep, [3], 'הנוכחית');
    assertError(d, d.rep, [7], 'הנוכחית');
    assertError(d, d.rep, [10], 'הנוכחית');
    d.hyp(formula('p'));			// 26. || p
    d.hyp(formula('p'));			// 27. ||| p
    d.hyp(formula('p'));			// 28. |||| p
    assertError(d, d.rep, [4], 'אחרת');
    assertError(d, d.rep, [8], 'אחרת');
    assertError(d, d.rep, [11], 'אחרת');
    assertError(d, d.rep, [12], 'אחרת');
    assertError(d, d.rep, [14], 'אחרת');
    assertError(d, d.rep, [16], 'אחרת');
    assertError(d, d.rep, [18], 'אחרת');
    assertError(d, d.rep, [20], 'אחרת');
    d.rep(10);					// 29. |||| p>q
    d.rep(25);					// 30. |||| p>p
    assertFormulasEqual(formula('p'), d.get(1));
    assertFormulasEqual(formula('q'), d.get(2));
    assertFormulasEqual(formula('p>q'), d.get(10));
    assertFormulasEqual(formula('p>p'), d.get(18));
    assertFormulasEqual(formula('p'), d.get(26));
    assertFormulasEqual(formula('p>p'), d.get(30));

    // ----------------
    // pop tests 
    // ----------------

    var d = deduction('p');
    d.pop();
    assertEquals(0, d.idx());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(0, d.idx());
    assertEquals(0, d.nesting());
    assertEquals(d.symbols.length, d.formulas.length);

    var d = deduction();
    d.hyp(formula('q'));
    d.impI();
    d.pop();
    assertEquals(1, d.idx());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(0, d.idx());
    assertEquals(0, d.nesting());
    assertEquals(d.symbols.length, d.formulas.length);

    var d = deduction('p','p>q');
    d.impE(1,2); // 3. q
    d.hyp(formula('r'));  // 4. | r
    d.rep(3);    // 5. | q
    d.pop();
    assertEquals(4, d.idx());
    assertEquals(1, d.nesting());
    d.rep(3);
    d.impI(); // 6. r>q
    assertEquals(6, d.idx());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(5, d.idx());
    assertEquals(1, d.nesting());
    d.impI(); // 6. r>q
    assertEquals(6, d.idx());
    assertEquals(0, d.nesting());
    d.conI(1,6) // 7. p-(r>q)
    d.pop();
    assertEquals(6, d.idx());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(5, d.idx());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(4, d.idx());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(3, d.idx());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(2, d.idx());
    assertEquals(0, d.nesting());
    d.impE(1,2); // 3. q
    assertEquals(3, d.idx());
    assertEquals(0, d.nesting());
    assertEquals(d.symbols.length, d.formulas.length);

    var d = deduction('p','p>q');		// 1. p
 						// 2. p>q
    d.impE(1,2); 				// 3. q
    d.hyp(formula('r'));  			// 4. | r
    d.hyp(formula('r'));  			// 5. || r
    d.hyp(formula('r'));  			// 6. ||| r
    d.pop();
    d.pop();					// 1. p
                                                // 2. p>q
                                                // 3. q
                                                // 4. | r
    assertEquals(4, d.idx());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('r'), d.get(4));
    d.hyp(formula('r'));  			// 5. || r
    d.hyp(formula('r'));  			// 6. ||| r
    d.impI();					// 7. || r>r
    d.hyp(formula('q'));  			// 8. ||| q
    d.pop();
    d.pop();					// 1. p
                                                // 2. p>q
                                                // 3. q
                                                // 4. | r
                                                // 5. || r
                                                // 6. ||| r
    assertEquals(6, d.idx());
    assertEquals(3, d.nesting());
    assertFormulasEqual(formula('r'), d.get(6));
    assertUndefined(d.rep(8));
    assertEquals(0, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);
    assertEquals(0, d.nestingLevels[3]);
    assertEquals(1, d.nestingLevels[4]);
    assertEquals(2, d.nestingLevels[5]);
    assertEquals(3, d.nestingLevels[6]);
    d.rep(1); 		 			// 7. ||| p
    d.impI();					// 8. || r>p
    d.impI();					// 9. | r>(r>p)
    d.pop();					// 8. || r>p
    assertEquals(8, d.idx());
    assertEquals(2, d.nesting());
    assertFormulasEqual(formula('r>p'), d.get(8));
    assertError(d, d.rep, [7], 'אחרת');
    d.impI();					// 9. | r>(r>p)
    d.pop();
    d.pop();
    d.pop();
    d.pop();
    d.pop();					// 1. p
                                                // 2. p>q
                                                // 3. q
                                                // 4. | r
    assertEquals(4, d.idx());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('r'), d.get(4));
    d.rep(1); 		 			// 5. | p
    d.impI();					// 6. r>p
    d.pop();					// 5. | p
    assertEquals(5, d.idx());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('p'), d.get(5));
    assertUndefined(d.get(6));
    assertUndefined(d.get(7));
    assertUndefined(d.rep(6));
    assertUndefined(d.rep(7));
    d.impI();					// 6. r>p
    assertFormulasEqual(formula('r>p'), d.get(6));
    assertEquals(6, d.idx());
    assertEquals(0, d.nesting());
    assertEquals(0, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);
    assertEquals(0, d.nestingLevels[3]);
    assertEquals(1, d.nestingLevels[4]);
    assertEquals(1, d.nestingLevels[5]);
    assertEquals(0, d.nestingLevels[6]);
    assertEquals(d.symbols.length, d.formulas.length);

    // ------------------------
    // simple deduction tests 
    // ------------------------

    var d = deduction('p>q', 'p');
    d.impE(1,2);
    assertFormulasEqual(formula('q'), d.get(3));
    d.conI(2,3);
    assertFormulasEqual(formula('p-q'), d.get(4));
    d.conE(4);
    assertFormulasEqual(formula('p'), d.get(5));
    assertFormulasEqual(formula('q'), d.get(6));
    assertUndefined(d.conE(6));
    assertUndefined(d.conE(7));
    d.disI(4, formula('~p'));
    assertFormulasEqual(formula('(p-q)v~p'), d.get(7));
    assertUndefined(d.conE(0));
    assertEquals(d.symbols.length, d.formulas.length);

    var d = deduction('p>r', 'q>r', 's', 's>(pvq)');
    assertUndefined(d.impE(1,2));
    d.impE(3,4);
    assertFormulasEqual(formula('pvq'), d.get(5));
    assertUndefined(d.disE(1,2,3));
    d.disE(1,2,5);
    assertFormulasEqual(formula('r'), d.get(6));
    d.conI(6,3);
    assertFormulasEqual(formula('r-s'), d.get(7));
    assertEquals(d.symbols.length, d.formulas.length);

    // ------------------------
    // complex deduction tests 
    // ------------------------

    // deducing pv~p
    var d = deduction();
    d.hyp(formula('~(pv~p)'));		// 1.  | ~(pv~p)
    d.hyp(formula('p'));		// 2.  || p
    d.disI(2, formula('~p'));		// 3.  || pv~p
    d.rep(1);  				// 4.  || ~(pv~p)
    d.conI(3,4);			// 5.  || (pv~p)-~(pv~p)
    d.negI();				// 6.  | ~p
    d.disI(6, formula('p'));		// 7.  | ~pvp
    d.conI(1,7);			// 8.  | (pv~p)-~(pv~p)
    d.negI();				// 9.  ~~(pv~p)
    d.negE(9);				// 10. pv~p
    assertFormulasEqual(d.get(4), formula('~(pv~p)'));
    assertFormulasEqual(d.get(6), formula('~p'));
    assertFormulasEqual(d.get(9), formula('~~(pv~p)'));
    assertFormulasEqual(d.get(10), formula('pv~p'));
    assertEquals(d.symbols.length, d.formulas.length);

    // deducing p>(q>p)
    var d = deduction();
    d.hyp(formula('p'));		// 1. | p
    d.hyp(formula('q'));		// 2. || q 
    d.rep(1);  				// 3. || p
    d.impI();  				// 4. | q>p
    d.impI();  				// 5. p>(q>p)
    assertFormulasEqual(d.get(3), formula('p'));
    assertFormulasEqual(d.get(4), formula('q>p'));
    assertFormulasEqual(d.get(5), formula('p>(q>p)'));
    assertEquals(d.symbols.length, d.formulas.length);

    // deducing (p-~p)>q
    var d = deduction();
    d.hyp(formula('p-~p'));		// 1. | p-~p
    d.hyp(formula('~q'));		// 2. || ~q 
    d.rep(1);  				// 3. || p-~p
    d.negI();  				// 4. | ~~q 
    d.negE(4);  			// 5. | q 
    d.impI();  				// 6. (p-~p)>q
    assertFormulasEqual(d.get(2), formula('~q'));
    assertFormulasEqual(d.get(4), formula('~~q'));
    assertFormulasEqual(d.get(6), formula('(p-~p)>q'));
    assertEquals(d.symbols.length, d.formulas.length);

    // deducing p>(q>p), with deletions
    var d = deduction();
    d.hyp(formula('p'));		// 1. | p
    d.hyp(formula('p'));		// 2. || p 
    d.pop();				// 1. | p
    d.hyp(formula('q'));		// 2. || q 
    d.rep(1);  				// 3. || p
    d.impI();  				// 4. | q>p
    d.impI();  				// 5. p>(q>p)
    d.pop();  				// 4. | q>p
    d.pop();  				// 3. || p
    d.impI();  				// 4. | q>p
    d.impI();  				// 5. p>(q>p)
    assertFormulasEqual(formula('p'), d.get(1));
    assertFormulasEqual(formula('q'), d.get(2));
    assertFormulasEqual(formula('p'), d.get(3));
    assertFormulasEqual(formula('q>p'), d.get(4));
    assertFormulasEqual(formula('p>(q>p)'), d.get(5));
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(2, d.nestingLevels[2]);
    assertEquals(2, d.nestingLevels[3]);
    assertEquals(1, d.nestingLevels[4]);
    assertEquals(0, d.nestingLevels[5]);
    assertEquals(d.symbols.length, d.formulas.length);

    // deducing (p-~p)>q, with failed rules
    var d = deduction();
    d.hyp(formula('p-~p'));		// 1. | p-~p
    assertError(d, d.rep, [1], 'הנוכחית');
    d.hyp(formula('~q'));		// 2. || ~q 
    d.negI();
    d.rep(1);  				// 3. || p-~p
    assertUndefined(d.impE(1,2));
    assertUndefined(d.conI(1,2));
    d.negI();  				// 4. | ~~q 
    assertUndefined(d.negI());
    assertError(d, d.rep, [3], 'אחרת');
    d.negE(4);  			// 5. | q 
    assertUndefined(d.negI());
    assertError(d, d.rep, [3], 'אחרת');
    d.impI();  				// 6. (p-~p)>q
    assertError(d, d.rep, [3], 'אחרת');
    assertError(d, d.rep, [1], 'אחרת');
    assertError(d, d.rep, [5], 'אחרת');
    assertUndefined(d.negI());
    assertUndefined(d.impE(1,6));
    assertUndefined(d.conI(1,6));
    assertUndefined(d.conI(3,4));
    assertFormulasEqual(d.get(1), formula('p-~p'));
    assertFormulasEqual(d.get(2), formula('~q'));
    assertFormulasEqual(d.get(3), formula('p-~p'));
    assertFormulasEqual(d.get(4), formula('~~q'));
    assertFormulasEqual(d.get(5), formula('q'));
    assertFormulasEqual(d.get(6), formula('(p-~p)>q'));
    assertEquals(d.symbols.length, d.formulas.length);

// ===== tests end =====

} catch (e) {
    error = true;
    var lines = e.stack.split('\n');
    console.log(e + ' (at line ' + getErrorLineNumber(e) + ')');
}

// summary

console.log('---  Ran ' + count + ' tests in ' + ((new Date().getTime() - t1) / 1000.0) + 's');
if (!error) console.log('---  OK');
else console.log('---  Fail');

// =============
// utils
// =============

function formula(f) {
    return new Formula(form(f));
}

function predicateFormula(f) {
    return new PredicateFormula(form(f));
}

function deduction() {
    var d = new Deduction();
    for (var i = 0; i < arguments.length; i++) {
        d.push(formula(arguments[i]));
    }
    return d;
}

function form(formula) {
    var result = formula;
    for (con in symbols) {
        result = result.replace(new RegExp(con, 'g'), symbols[con]);
    }
    return result;
}

function analyzed(formula) {
    return analyze(form(formula));
}

function getErrorLineNumber(e) {
    var lines = e.stack.split('\n');
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].indexOf('Object.<anonymous>') > -1) {
            return lines[i].split(':')[1];
        }
    }
}

// =============
// asserts
// =============

function assertForm(f, con, sf1, sf2, cls) {
    if (!cls) cls = Formula;
    frm = new cls(form(f));
    assertEquals(con? symbols[con] : null, frm.con);
    assertEquals(form(sf1), frm.sf1 == null? '' : frm.sf1.lit);
    assertEquals(form(sf2), frm.sf2 == null? '' : frm.sf2.lit);
    return frm;
}

function assertPredicateForm(f, con, sf1, sf2, quantifier, quantified) {
    frm = assertForm(f, con, sf1, sf2, PredicateFormula);
    assertEquals(quantifier? symbols[quantifier] : null, frm.quantifier);
    assertEquals(quantified? quantified : null, frm.quantified);
}

function assertInvalidForm(f, cls) {
    if (!cls) cls = Formula;
    err = '';
    try { new cls(form(f)); }
    catch (e) { err = e; }
    assertFalse(err == '');
}

function assertInvalidArgument(string) {
    err = '';
    try { new Argument(form(string)); }
    catch (e) { err = e; }
    assertFalse(err == '');
}

function assertError(obj, func, args, msg) {
    err = '';
    try { func.apply(obj, args); }
    catch (e) { err = e; }
    try { if (msg) assertTrue(err.toString().indexOf(msg) > -1); }
    catch (e) { throw Error('expected ' + msg + ' in error, got ' + err); }
    if (!msg) assertFalse(err == '');
}

function assertTrue(a) {
    assertEquals(true, a);
}

function assertFalse(a) {
    assertEquals(false, a);
}

function assertUndefined(a) {
    assertEquals(undefined, a);
}

function assertFormulasEqual(f1, f2) {
    try {
        assertTrue(f1.equals(f2));
    } catch (e) {
        throw new Error('expected ' + f1 + ', got ' + f2);
    }
}

function assertListsEqual(l, k) {
    try {
        assertEquals(l.length, k.length);
        for (var i = 0; i < l.length; i++) {
            assertTrue(l[i].equals(k[i]));
        }
    } catch (e) {
        throw new Error('expected ' + l + ', got ' + k);
    }
}

function assertEquals(a, b) {
    count++;
    if (a !== b) {
        throw new Error('expected ' + a + ', got ' + b);
    }
}

