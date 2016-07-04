// =============
// imports
// =============

deduction = require('./deduction2.js');
var analyze = deduction.analyze;
var equal = deduction.equal;
var isNegOf = deduction.isNegationOf;
var isCnt = deduction.isContradiction;
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
    assertTrue(equal(form('(p,r),(q,s)'), form('((s,q),(r,p))')));

    assertFalse(equal(form('p'), form('q')));
    assertFalse(equal(form('p>r'), form('r>p')));
    assertFalse(equal(form('(p,q)-r'), form('p,(q-r)')));
    assertFalse(equal(form('(p-r)=(q,s)'), form('((s-q)=(r,p))')));

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

function assertEquals(a, b) {
    count++;
    if (a !== b) {
        throw new Error('expected ' + a + ', got ' + b);
    }
}

