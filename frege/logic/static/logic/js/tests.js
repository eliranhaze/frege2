deduction = require('./deduction2.js');

var analyze = deduction.analyze;
var count = 0;
var error = false;
var t1 = new Date().getTime();

// =============
// tests
// =============

try {

// ===== tests start =====
    assertEquals(analyze('~p').con, '~');
    assertEquals(analyze('~p').sf1, 'p');
    assertEquals(analyze('~p').sf2, '');

// ===== tests end =====

} catch (e) {
    error = true;
    console.log(e + "")
}

// summary

console.log('---  Ran ' + count + ' tests in ' + ((new Date().getTime() - t1) / 1000.0) + 's');
if (!error) console.log('---  OK');
else console.log('---  Fail');

// =============
// utils
// =============

function assertEquals(a, b) {
    count++;
    if (a !== b) {
        throw new Error('"' + a + '" not equals "' + b + '"');
    }
}
