
// =============
// imports
// =============

var lib = require('./deduction2.js');

var Formula = lib.Formula;
var Deduction = lib.Deduction;

var currentNesting = lib.currentNesting;
var endNesting = lib.endNesting;
var startNesting = lib.startNesting;
var isOpenNested = lib.isOpenNested;
var isOnCurrentLevel = lib.isOnCurrentLevel;
var getNesting = lib.getNesting;

var connectives = {
    '~': lib.NEG,
    '-': lib.CON,
    ',': lib.DIS,
    '>': lib.IMP,
    '=': lib.EQV,
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
    assertForm('~~p=~((p-q),(q,s))', '=', '~~p', '~((p-q),(q,s))');

    // more scrutiny
    var sf1_sf1 = '~p';
    var sf1_sf2 = 'q';
    var sf1 = '(' + sf1_sf1 + '),(' + sf1_sf2 + ')';
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
    assertEquals(frm.sf1.con, form(','));
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
    assertInvalidForm('(~p>~q),(p=r');
    assertInvalidForm('(~p>~q),p=r');
    assertInvalidForm('(~p>~q),p=r)');
    assertInvalidForm('(~p>~q),(p=r~)');
    assertInvalidForm('(~p>~q),(p=r)~');
    assertInvalidForm('(~p>~q)~,(p=r)');

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
    assertTrue(formula('~((r-q),(p=q))').isNegationOf(formula('(q=p),(q-r)')));

    assertFalse(formula('~((r-q),(p=q))').isNegationOf(formula('(q=p)-(q-r)')));
    assertFalse(formula('~(r>q)').isNegationOf(formula('q>r')));
    assertFalse(formula('~~p').isNegationOf(formula('p')));
    assertFalse(formula('~q').isNegationOf(formula('p')));
    assertFalse(formula('~q,p').isNegationOf(formula('q,p')));

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
    assertFalse(formula('~p,p').isContradiction());
    assertFalse(formula('~p>p').isContradiction());
    assertFalse(formula('(p>q)-(~p>q)').isContradiction());

    // ----------------
    // equals tests 
    // ----------------

    assertTrue(formula('p').equals(formula('p')));
    assertTrue(formula('p,r').equals(formula('p,r')));
    assertTrue(formula('p,r').equals(formula('r,p')));
    assertTrue(formula('(p,r)').equals(formula('r,p')));
    assertTrue(formula('(p,r)').equals(formula('(r,p)')));
    assertTrue(formula('~(p,r)').equals(formula('~(r,p)')));
    assertTrue(formula('~(p,~r)').equals(formula('~(~r,p)')));
    assertTrue(formula('(p,r),(q,s)').equals(formula('((s,q),(r,p))')));

    assertFalse(formula('p').equals(formula('q')));
    assertFalse(formula('~p').equals(formula('~q')));
    assertFalse(formula('p>r').equals(formula('r>p')));
    assertFalse(formula('(p,q)-r').equals(formula('p,(q-r)')));
    assertFalse(formula('(p-r)=(q,s)').equals(formula('((s-q)=(r,p))')));
    assertFalse(formula('~(p,r)').equals(formula('~r,p')));
    assertFalse(formula('~p,r').equals(formula('~r,p')));
    assertFalse(formula('~p,r').equals(formula('~(p,r)')));

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
        deduction('~((p,q)=(p-~r))>((q>r)=~~p)', '~((q,p)=(~r-p))').
        impE(1,2).equals(formula('(q>r)=~~p'))
    );

    assertUndefined(deduction('p>q','q').impE(1,2));
    assertUndefined(deduction('p>q','p').impE(0,2));
    assertUndefined(deduction('p>q','p').impE(1,3));
    assertUndefined(deduction('p>q','p').impE(2,4));
    assertUndefined(deduction('p>q','~p').impE(1,2));
    assertUndefined(deduction('p>q','p>q').impE(1,2));
    assertUndefined(deduction('(p-q)>q','p,q').impE(1,2));
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
        deduction('p>r', 'q>r', 'p,q').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('p>r', 'q>r', 'p,q').disE(2,3,1)
    );
    assertFormulasEqual(
        formula('r'),
        deduction('p>r', 'q>r', 'p,q').disE(3,1,2)
    );
    assertFormulasEqual(
        formula('q'),
        deduction('p>q', 'r>q', 'p,r').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('~~(r)'),
        deduction('(p-q)>(~~r)', '(q,s)>~~(r)', '(s,q),(q-p)').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('q=p'),
        deduction('(~r>(p=q))', '~~~(~s,p)>(q=p)', '((~r),~~~(p,~s))').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('r,s'),
        deduction('(p>(s,r))', '~p>(r,s)', 'p,~p').disE(1,2,3)
    );
    assertFormulasEqual(
        formula('r,s'),
        deduction('(p>(s,r))', 'p>(r,s)', 'p,p').disE(1,2,3)
    );

    assertUndefined(deduction('(p>(s,r))', '~p=(r,s)', 'p,~p').disE(1,2,3));
    assertUndefined(deduction('(p>(s,r))', 'p=(r,s)', 'p,~p').disE(1,2,3));
    assertUndefined(deduction('(p>(s,r))', 'q=(r,s)', 'p,r').disE(1,2,3));
    assertUndefined(deduction('(p>(s,r))', '~p=(r=s)', 'p,~p').disE(1,2,3));
    assertUndefined(deduction('p>q', 'r>q', 'p,r').disE(0,2,3));
    assertUndefined(deduction('p>q', 'r>q', 'p,r').disE(1,2,10));

    // ----------------
    // eqvE tests 
    // ----------------

    assertListsEqual(
        [formula('q>p'), formula('p>q')],
        deduction('q=p').eqvE(1)
    );
    assertListsEqual(
        [formula('(p=q)>~(r,~s)'), formula('~(r,~s)>(p=q)')],
        deduction('(p=q)=~(r,~s)').eqvE(1)
    );

    assertUndefined(deduction('p').eqvE(1));
    assertUndefined(deduction('p,q').eqvE(1));
    assertUndefined(deduction('p>(s,r)').eqvE(1));
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
        formula('~s,~r'),
        deduction('~~(~s,~r)').negE(1)
    );

    assertUndefined(deduction('p>(s,r)').negE(1));
    assertUndefined(deduction('~p').negE(1));
    assertUndefined(deduction('~~s>p').negE(1));
    assertUndefined(deduction('p,~~s').negE(1));
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
        formula('(p>q)-(~q,r)'),
        deduction('p>q', '~q,r').conI(1,2)
    );
    assertFormulasEqual(
        formula('(r-q)-~p'),
        deduction('r-q', '~p').conI(1,2)
    );

    // ----------------
    // disI tests 
    // ----------------

    assertFormulasEqual(
        formula('~~r,p'),
        deduction('~~r').disI(1,formula('p'))
    );
    assertFormulasEqual(
        formula('(p>q),(~q,r)'),
        deduction('p>q').disI(1,formula('~q,r'))
    );
    assertFormulasEqual(
        formula('(r,q),~p'),
        deduction('r,q').disI(1,formula('~p'))
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
        formula('((~~r,p),s)=~(s-p)'),
        deduction('((~~r,p),s)>~(s-p)', '~(p-s)>(s,(~~r,p))').eqvI(1,2)
    );

    assertUndefined(deduction('p>q', 'p>q').eqvI(1,2));
    assertUndefined(deduction('p>q', 'q>~p').eqvI(1,2));
    assertUndefined(deduction('(p>q)>r', '(r>p)>q').eqvI(1,2));
    assertUndefined(deduction('(q-p)>(s=r)', '(r,s)>(p-q)').eqvI(1,2));
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
    d.hyp(formula('(~q,p)-~(p,~q)'));
    assertFormulasEqual(formula('~((~q,p)-~(p,~q))'), d.negI());
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);

    assertUndefined(deduction().negI());
    assertUndefined(deduction('p-~p').negI());
    assertUndefined(deduction('p-~p', 'p').negI());
    var d = deduction();
    d.hyp(formula('p,~p'));
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
    assertFormulasEqual(formula('p'), d.getFormula(1));
    assertFormulasEqual(formula('q'), d.getFormula(2));
    assertFormulasEqual(formula('p>q'), d.getFormula(10));
    assertFormulasEqual(formula('p>p'), d.getFormula(18));
    assertFormulasEqual(formula('p'), d.getFormula(26));
    assertFormulasEqual(formula('p>p'), d.getFormula(30));

    // ----------------
    // pop tests 
    // ----------------

    var d = deduction('p');
    d.pop();
    assertEquals(0, d.index());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(0, d.index());
    assertEquals(0, d.nesting());

    var d = deduction();
    d.hyp(formula('q'));
    d.impI();
    d.pop();
    assertEquals(1, d.index());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(0, d.index());
    assertEquals(0, d.nesting());

    var d = deduction('p','p>q');
    d.impE(1,2); // 3. q
    d.hyp(formula('r'));  // 4. | r
    d.rep(3);    // 5. | q
    d.pop();
    assertEquals(4, d.index());
    assertEquals(1, d.nesting());
    d.rep(3);
    d.impI(); // 6. r>q
    assertEquals(6, d.index());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(5, d.index());
    assertEquals(1, d.nesting());
    d.impI(); // 6. r>q
    assertEquals(6, d.index());
    assertEquals(0, d.nesting());
    d.conI(1,6) // 7. p-(r>q)
    d.pop();
    assertEquals(6, d.index());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(5, d.index());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(4, d.index());
    assertEquals(1, d.nesting());
    d.pop();
    assertEquals(3, d.index());
    assertEquals(0, d.nesting());
    d.pop();
    assertEquals(2, d.index());
    assertEquals(0, d.nesting());
    d.impE(1,2); // 3. q
    assertEquals(3, d.index());
    assertEquals(0, d.nesting());

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
    assertEquals(4, d.index());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('r'), d.getFormula(4));
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
    assertEquals(6, d.index());
    assertEquals(3, d.nesting());
    assertFormulasEqual(formula('r'), d.getFormula(6));
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
    assertEquals(8, d.index());
    assertEquals(2, d.nesting());
    assertFormulasEqual(formula('r>p'), d.getFormula(8));
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
    assertEquals(4, d.index());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('r'), d.getFormula(4));
    d.rep(1); 		 			// 5. | p
    d.impI();					// 6. r>p
    d.pop();					// 5. | p
    assertEquals(5, d.index());
    assertEquals(1, d.nesting());
    assertFormulasEqual(formula('p'), d.getFormula(5));
    assertUndefined(d.getFormula(6));
    assertUndefined(d.getFormula(7));
    assertUndefined(d.rep(6));
    assertUndefined(d.rep(7));
    d.impI();					// 6. r>p
    assertFormulasEqual(formula('r>p'), d.getFormula(6));
    assertEquals(6, d.index());
    assertEquals(0, d.nesting());
    assertEquals(0, d.nestingLevels[1]);
    assertEquals(0, d.nestingLevels[2]);
    assertEquals(0, d.nestingLevels[3]);
    assertEquals(1, d.nestingLevels[4]);
    assertEquals(1, d.nestingLevels[5]);
    assertEquals(0, d.nestingLevels[6]);

    // ------------------------
    // simple deduction tests 
    // ------------------------

    var d = deduction('p>q', 'p');
    d.impE(1,2);
    assertFormulasEqual(formula('q'), d.getFormula(3));
    d.conI(2,3);
    assertFormulasEqual(formula('p-q'), d.getFormula(4));
    d.conE(4);
    assertFormulasEqual(formula('p'), d.getFormula(5));
    assertFormulasEqual(formula('q'), d.getFormula(6));
    assertUndefined(d.conE(6));
    assertUndefined(d.conE(7));
    d.disI(4, formula('~p'));
    assertFormulasEqual(formula('(p-q),~p'), d.getFormula(7));
    assertUndefined(d.conE(0));

    var d = deduction('p>r', 'q>r', 's', 's>(p,q)');
    assertUndefined(d.impE(1,2));
    d.impE(3,4);
    assertFormulasEqual(formula('p,q'), d.getFormula(5));
    assertUndefined(d.disE(1,2,3));
    d.disE(1,2,5);
    assertFormulasEqual(formula('r'), d.getFormula(6));
    d.conI(6,3);
    assertFormulasEqual(formula('r-s'), d.getFormula(7));

    // ------------------------
    // complex deduction tests 
    // ------------------------

    // deducing p,~p
    var d = deduction();
    d.hyp(formula('~(p,~p)'));		// 1.  | ~(p,~p)
    d.hyp(formula('p'));		// 2.  || p
    d.disI(2, formula('~p'));		// 3.  || p,~p
    d.rep(1);  				// 4.  || ~(p,~p)
    d.conI(3,4);			// 5.  || (p,~p)-~(p,~p)
    d.negI();				// 6.  | ~p
    d.disI(6, formula('p'));		// 7.  | ~p,p
    d.conI(1,7);			// 8.  | (p,~p)-~(p,~p)
    d.negI();				// 9.  ~~(p,~p)
    d.negE(9);				// 10. p,~p
    assertFormulasEqual(d.getFormula(4), formula('~(p,~p)'));
    assertFormulasEqual(d.getFormula(6), formula('~p'));
    assertFormulasEqual(d.getFormula(9), formula('~~(p,~p)'));
    assertFormulasEqual(d.getFormula(10), formula('p,~p'));

    // deducing p>(q>p)
    var d = deduction();
    d.hyp(formula('p'));		// 1. | p
    d.hyp(formula('q'));		// 2. || q 
    d.rep(1);  				// 3. || p
    d.impI();  				// 4. | q>p
    d.impI();  				// 5. p>(q>p)
    assertFormulasEqual(d.getFormula(3), formula('p'));
    assertFormulasEqual(d.getFormula(4), formula('q>p'));
    assertFormulasEqual(d.getFormula(5), formula('p>(q>p)'));

    // deducing (p-~p)>q
    var d = deduction();
    d.hyp(formula('p-~p'));		// 1. | p-~p
    d.hyp(formula('~q'));		// 2. || ~q 
    d.rep(1);  				// 3. || p-~p
    d.negI();  				// 4. | ~~q 
    d.negE(4);  			// 5. | q 
    d.impI();  				// 6. (p-~p)>q
    assertFormulasEqual(d.getFormula(2), formula('~q'));
    assertFormulasEqual(d.getFormula(4), formula('~~q'));
    assertFormulasEqual(d.getFormula(6), formula('(p-~p)>q'));

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
    assertFormulasEqual(formula('p'), d.getFormula(1));
    assertFormulasEqual(formula('q'), d.getFormula(2));
    assertFormulasEqual(formula('p'), d.getFormula(3));
    assertFormulasEqual(formula('q>p'), d.getFormula(4));
    assertFormulasEqual(formula('p>(q>p)'), d.getFormula(5));
    assertEquals(1, d.nestingLevels[1]);
    assertEquals(2, d.nestingLevels[2]);
    assertEquals(2, d.nestingLevels[3]);
    assertEquals(1, d.nestingLevels[4]);
    assertEquals(0, d.nestingLevels[5]);

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
    assertFormulasEqual(d.getFormula(1), formula('p-~p'));
    assertFormulasEqual(d.getFormula(2), formula('~q'));
    assertFormulasEqual(d.getFormula(3), formula('p-~p'));
    assertFormulasEqual(d.getFormula(4), formula('~~q'));
    assertFormulasEqual(d.getFormula(5), formula('q'));
    assertFormulasEqual(d.getFormula(6), formula('(p-~p)>q'));

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

function deduction() {
    var d = new Deduction();
    for (var i = 0; i < arguments.length; i++) {
        d.push(formula(arguments[i])); 
    }
    return d;
}

function form(formula) {
    var result = formula;
    for (con in connectives) {
        result = result.replace(new RegExp(con, 'g'), connectives[con]);
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

function assertForm(f, con, sf1, sf2) {
    frm = new Formula(form(f));
    assertEquals(connectives[con], frm.con);
    assertEquals(form(sf1), frm.sf1 == null? '' : frm.sf1.lit);
    assertEquals(form(sf2), frm.sf2 == null? '' : frm.sf2.lit);
}

function assertInvalidForm(f) {
    err = '';
    try { new Formula(f); }
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

