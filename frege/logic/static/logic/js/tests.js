
// =============
// imports
// =============

deduction = require('./deduction2.js');

var analyze = deduction.analyze;
var equal = deduction.equal;
var isNegOf = deduction.isNegationOf;
var isCnt = deduction.isContradiction;

var initState = deduction.initState;
var rownum = deduction.rownum;
var initState = deduction.initState;
var currentNesting = deduction.currentNesting;
var endNesting = deduction.endNesting;
var startNesting = deduction.startNesting;
var isOpenNested = deduction.isOpenNested;
var isOnCurrentLevel = deduction.isOnCurrentLevel;
var getNesting = deduction.getNesting;

var impE = deduction.impE;
var conE = deduction.conE;
var disE = deduction.disE;
var eqvE = deduction.eqvE;
var negE = deduction.negE;
var impI = deduction.impI;
var conI = deduction.conI;
var disI = deduction.disI;
var eqvI = deduction.eqvI;
var negI = deduction.negI;

var connectives = {
    '~': deduction.NEG,
    '-': deduction.CON,
    ',': deduction.DIS,
    '>': deduction.IMP,
    '=': deduction.EQV,
};

// =============
// tests
// =============

var count = 0;
var error = false;
var t1 = new Date().getTime();

try {

// ===== tests start =====

    // ----------------
    // analyze tests 
    // ----------------

    // valid cases
    assertForm('~p', '~', 'p', '');
    assertForm('~~~p', '~', '~~p', '');
    assertForm('~(~~p)', '~', '(~~p)', '');
    assertForm('p-q', '-', 'p', 'q');
    assertForm('p-~~q', '-', 'p', '~~q');
    assertForm('(p-q)>~r', '>', '(p-q)', '~r');
    assertForm('((~p)-~r)>p', '>', '((~p)-~r)', 'p');
    assertForm('~~p=~((p-q),(q,s))', '=', '~~p', '~((p-q),(q,s))');

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
    // isNegOf tests 
    // ----------------

    assertTrue(isNegOf(analyzed('~p'), analyzed('p')));
    assertTrue(isNegOf(analyzed('~~p'), analyzed('~p')));
    assertTrue(isNegOf(analyzed('(~p)'), analyzed('p')));
    assertTrue(isNegOf(analyzed('~(~p)'), analyzed('~p')));
    assertTrue(isNegOf(analyzed('~(~(~p))'), analyzed('~~p')));
    assertTrue(isNegOf(analyzed('(~(~(~p)))'), analyzed('~~p')));
    assertTrue(isNegOf(analyzed('~(r-q)'), analyzed('q-r')));
    assertTrue(isNegOf(analyzed('(~(r-q))'), analyzed('q-r')));
    assertTrue(isNegOf(analyzed('~(r-q)'), analyzed('(r-q)')));
    assertTrue(isNegOf(analyzed('~(r-q)'), analyzed('r-q')));
    assertTrue(isNegOf(analyzed('~((r-q),(p=q))'), analyzed('(q=p),(q-r)')));

    assertFalse(isNegOf(analyzed('~((r-q),(p=q))'), analyzed('(q=p)-(q-r)')));
    assertFalse(isNegOf(analyzed('~(r>q)'), analyzed('q>r')));
    assertFalse(isNegOf(analyzed('~~p'), analyzed('p')));
    assertFalse(isNegOf(analyzed('~q'), analyzed('p')));
    assertFalse(isNegOf(analyzed('~q,p'), analyzed('q,p')));

    // ----------------
    // isCnt tests 
    // ----------------

    assertTrue(isCnt(form('p-~p')));
    assertTrue(isCnt(form('~p-p')));
    assertTrue(isCnt(form('~~p-~p')));
    assertTrue(isCnt(form('~~p-~~~p')));
    assertTrue(isCnt(form('~(~(p))-~(~~p)')));
    assertTrue(isCnt(form('~(p>q)-(p>q)')));
    assertTrue(isCnt(form('(p>q)-~(p>q)')));
    assertTrue(isCnt(form('(p=q)-~(q=p)')));

    assertFalse(isCnt(form('p-p')));
    assertFalse(isCnt(form('~p-~p')));
    assertFalse(isCnt(form('~p,p')));
    assertFalse(isCnt(form('~p>p')));
    assertFalse(isCnt(form('(p>q)-(~p>q)')));

    // ----------------
    // equal tests 
    // ----------------

    assertTrue(equal(form('p'), form('p')));
    assertTrue(equal(form('p,r'), form('p,r')));
    assertTrue(equal(form('p,r'), form('r,p')));
    assertTrue(equal(form('(p,r)'), form('r,p')));
    assertTrue(equal(form('(p,r)'), form('(r,p)')));
    assertTrue(equal(form('~(p,r)'), form('~(r,p)')));
    assertTrue(equal(form('~(p,~r)'), form('~(~r,p)')));
    assertTrue(equal(form('(p,r),(q,s)'), form('((s,q),(r,p))')));

    assertFalse(equal(form('p'), form('q')));
    assertFalse(equal(form('p>r'), form('r>p')));
    assertFalse(equal(form('(p,q)-r'), form('p,(q-r)')));
    assertFalse(equal(form('(p-r)=(q,s)'), form('((s-q)=(r,p))')));
    assertFalse(equal(form('~(p,r)'), form('~r,p')));
    assertFalse(equal(form('~p,r'), form('~r,p')));
    assertFalse(equal(form('~p,r'), form('~(p,r)')));

    // ----------------
    // impE tests 
    // ----------------

    assertEquals(
        form('q'),
        impE(form('p>q'), form('p'))
    );
    assertEquals(
        form('q'),
        impE(form('p>q'), form('(p)'))
    );
    assertEquals(
        form('r>q'),
        impE(form('(p>q)>(r>q)'), form('p>q'))
    );
    assertEquals(
        form('r>q'),
        impE(form('(p>q)>(r>q)'), form('(p>q)'))
    );
    assertEquals(
        form('q'),
        impE(form('(p-q)>q'), form('q-p'))
    );
    assertEquals(
        form('(q>r)=~~p'),
        impE(form('~((p,q)=(p-~r))>((q>r)=~~p)'), form('~((p,q)=(p-~r))'))
    );

    assertUndefined(
        impE(form('p>q'), form('q'))
    );
    assertUndefined(
        impE(form('p>q'), form('~p'))
    );
    assertUndefined(
        impE(form('p>q'), form('p>q'))
    );
    assertUndefined(
        impE(form('(p-q)>q'), form('q,p'))
    );
    assertUndefined(
        impE(form('~(p-q)>q'), form('~p-q'))
    );
    assertUndefined(
        impE(form('(p-q)=q'), form('q-p'))
    );

    // ----------------
    // conE tests 
    // ----------------

    assertListsEqual(
        [form('q'), form('p')],
        conE(form('q-p'))
    );
    assertListsEqual(
        [form('~p'), form('~q')],
        conE(form('~p-~q'))
    );
    assertListsEqual(
        [form('~p-~q'), form('p-r')],
        conE(form('((~p-~q)-(p-r))'))
    );

    assertUndefined(
        conE(form('((~p-~q)>(p-r))'))
    );
    assertUndefined(
        conE(form('~(p-q)'))
    );

    assertUndefined(
        conE(form('p'))
    );

    // ----------------
    // disE tests 
    // ----------------

    assertEquals(
        form('r'),
        disE(form('p>r'), form('q>r'), form('p,q'))
    );
    assertEquals(
        form('~~(r)'),
        disE(form('(p-q)>(~~r)'), form('(q,s)>~~(r)'), form('(s,q),(q-p)'))
    );
    assertEquals(
        form('q=p'),
        disE(form('~r>(p=q)'), form('~~~(~s,p)>(q=p)'), form('((~r),~~~(p,~s))'))
    );
    assertEquals(
        form('r,s'),
        disE(form('p>(s,r)'), form('~p>(r,s)'), form('p,~p'))
    );
    assertEquals(
        form('r,s'),
        disE(form('p>(s,r)'), form('p>(r,s)'), form('p,p'))
    );

    assertUndefined(
        disE(form('p>(s,r)'), form('~p=(r,s)'), form('p,~p'))
    );
    assertUndefined(
        disE(form('p>(s,r)'), form('p=(r,s)'), form('p,~p'))
    );
    assertUndefined(
        disE(form('p>(s,r)'), form('q=(r,s)'), form('p,r'))
    );
    assertUndefined(
        disE(form('p>(s,r)'), form('~p=(r=s)'), form('p,~p'))
    );

    // ----------------
    // eqvE tests 
    // ----------------

    assertListsEqual(
        [form('q>p'), form('p>q')],
        eqvE(form('q=p'))
    );
    assertListsEqual(
        [form('(p=q)>~(r,~s)'), form('~(r,~s)>(p=q)')],
        eqvE(form('(p=q)=~(r,~s)'))
    );

    assertUndefined(
        eqvE(form('p'))
    );
    assertUndefined(
        eqvE(form('p,q'))
    );
    assertUndefined(
        eqvE(form('p>(s,r)'))
    );

    // ----------------
    // negE tests 
    // ----------------

    assertEquals(
        form('r'),
        negE(form('~~r'))
    );
    assertEquals(
        form('r'),
        negE(form('(~~r)'))
    );
    assertEquals(
        form('r'),
        negE(form('~~(r)'))
    );
    assertEquals(
        form('r'),
        negE(form('~(~r)'))
    );
    assertEquals(
        form('~r'),
        negE(form('~~~r'))
    );
    assertEquals(
        form('~r'),
        negE(form('~~(~r)'))
    );
    assertEquals(
        form('~s,~r'),
        negE(form('~~(~s,~r)'))
    );

    assertUndefined(
        negE(form('p>(s,r)'))
    );
    assertUndefined(
        negE(form('~p'))
    );
    assertUndefined(
        negE(form('~~s>p'))
    );
    assertUndefined(
        negE(form('p,~~s'))
    );

    // ----------------
    // conI tests 
    // ----------------

    assertEquals(
        form('~~r-p'),
        conI(form('~~r'), form('p'))
    );
    assertEquals(
        form('(p>q)-(~q,r)'),
        conI(form('p>q'), form('~q,r'))
    );
    assertEquals(
        form('(r-q)-~p'),
        conI(form('r-q'), form('~p'))
    );

    // ----------------
    // disI tests 
    // ----------------

    assertEquals(
        form('~~r,p'),
        disI(form('~~r'), form('p'))
    );
    assertEquals(
        form('(p>q),(~q,r)'),
        disI(form('p>q'), form('~q,r'))
    );
    assertEquals(
        form('(r,q),~p'),
        disI(form('r,q'), form('~p'))
    );

    // ----------------
    // eqvI tests 
    // ----------------

    assertEquals(
        form('p=q'),
        eqvI(form('p>q'), form('((q)>p)'))
    );
    assertEquals(
        form('p=(q)'),
        eqvI(form('p>(q)'), form('((q)>p)'))
    );
    assertEquals(
        form('~r=p'),
        eqvI(form('~r>p'), form('p>~r'))
    );
    assertEquals(
        form('(q-p)=(s=r)'),
        eqvI(form('(q-p)>(s=r)'), form('(r=s)>(p-q)'))
    );
    assertEquals(
        form('((~~r,p),s)=~(s-p)'),
        eqvI(form('((~~r,p),s)>~(s-p)'), form('~(p-s)>(s,(~~r,p))'))
    );

    assertUndefined(
        eqvI(form('p>q'), form('p>q'))
    );
    assertUndefined(
        eqvI(form('p>q'), form('q>~p'))
    );
    assertUndefined(
        eqvI(form('(p>q)>r'), form('(r>p)>q'))
    );
    assertUndefined(
        eqvI(form('(q-p)>(s=r)'), form('(r,s)>(p-q)'))
    );

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
    a = analyze(form(f));
    assertEquals(connectives[con], a.con);
    assertEquals(form(sf1), a.sf1);
    assertEquals(form(sf2), a.sf2);
}

function assertInvalidForm(f) {
    a = analyze(form(f));
    assertEquals('', a.con);
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

function assertListsEqual(l, k) {
    assertEquals(l.toString(), k.toString());
}

function assertEquals(a, b) {
    count++;
    if (a !== b) {
        throw new Error('expected ' + a + ', got ' + b);
    }
}

