/*
 * functions for handling natural deduction for propositional and predicate logic
 */

// ==========================
// constants
// ==========================

var NEG = '~';
var CON = '·';
var DIS = '∨';
var IMP = '⊃';
var EQV = '≡';

// ==========================
// deduction rules
// ==========================

// implication elimination
function impE(f1, f2) {
    if (f1.length > f2.length) {
        return _impE(f1, f2);
    }
    return _impE(f2, f1);   
}
function _impE(implication, antecedent) {
    a = analyze(implication);
    if (a.con === IMP && stripBrackets(a.sf1) === stripBrackets(antecedent)) {
        return stripBrackets(a.sf2);
    }
}

// conjunction elimination
function conE(f) {
    a = analyze(f);
    if (a.con === CON) {
        return [stripBrackets(a.sf1), stripBrackets(a.sf2)];
    }
}
// conjunction introduction
function conI(f1, f2) {
    return wrap(f1)+CON+wrap(f2);
}

// ==========================
// utils
// ==========================

// return the main connective and sub formula(s) of a formula
function analyze(f) {
    _f = stripBrackets(f);
    var maybe_neg = false;
    var nesting = 0;
    for (var i = 0; i < _f.length; i++) {
        var c = _f.charAt(i);
        if (c === ')') {
            nesting--;
        } else if (c === '(') {
            nesting++;
        } else if (nesting === 0) {
            // highest nesting level, check for main connective
            if (c === CON || c === DIS || c === IMP || c === EQV) {
                return {
                    con: c,
                    sf1: _f.slice(0, i),
                    sf2: _f.slice(i+1)
                };
            } else if (c === NEG) {
                // don't return here since binary connectives take precedence
                maybe_neg = true;
            }
        }
    }
    if (maybe_neg) {
        return {
            con: NEG,
            sf1: _f.slice(1),
            sf2: ''
        }
    }
    return {
        con: '',
        sf1: '',
        sf2: ''
    };
}

// strip outmost brackets from a formula
function stripBrackets(f) {
    if (f.charAt(0) === '(' && f.charAt(f.length-1) === ')') {
        // brackets detected, make sure they can be stripped 
        var nesting = 0;
        for (var i = 0; i < f.length; i++) {
            var c = f.charAt(i);
            if (c === ')') {
                nesting--;
                if (nesting === 0) {
                    // closure found for the opening bracket, only strip if it's last
                    if (i === f.length - 1) { 
                        // strip recursively
                        return stripBrackets(f.slice(1, f.length - 1));
                    }
                    return f;
                }
            } else if (c === '(') {
                nesting++;
            }
        }   
    }
    return f;
}

// wrap a formula with brackets if needed
function wrap(f) {
    if (f.length > 2) {
        return '('+f+')';
    }
    return f;
}

// ==========================
// user interaction
// ==========================

// general function for applying a rule, gets rule-specific parameters and callbacks
function applyRule(ruleFunc, numLines, ruleSymbolFunc) {
    errmsg("");
    // validate selection
    if (numLines > 0) {
        checked = getChecked();
        if (checked.length != numLines) {
            words = ["", "שורה אחת", "שתי שורות", "שלוש שורות"];
            return errmsg("יש לבחור "+words[numLines]+" בדיוק על מנת להשתמש בכלל זה");
        }
    }
    // apply the rule
    consq = ruleFunc.apply(this, getLines(checked));
    if (consq) {
        // get new line number
        var n = $("#deduction >tbody >tr").length + 1;
        var symbol = ruleSymbolFunc(checked);
        // add the new line(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (i = 0; i < consq.length; i++) {
            addLine(n+i, consq[i], symbol);
        }
        // remove selection
        $("input[type=checkbox]").prop("checked", false);
    } else {
        errmsg("לא ניתן להשתמש בכלל עבור השורות שנבחרו");
    }
}

// add a deduction line with number and symbol
function addLine(n, content, symbol) {
    $('#deduction tr:last').after(
        '<tr>'+
          '<td class="dd-num""><input type="checkbox" id="cb'+n+'" name="'+n+'">'+n+'. </input></td>'+
          '<td id="f'+n+'">'+content+'</td>'+
          '<td class="dd-just">'+symbol+'</td>'+
        '</tr>'
    );
}

// symbol functions
function symbolImpE(lineNums) {
    return "E ⊃ " + lineNums[0] + "," + lineNums[1];
}
function symbolConE(lineNums) {
    return "E · " + lineNums[0];
}
function symbolConI(lineNums) {
    return "I · " + lineNums[0] + "," + lineNums[1];
}

// utils
function getLines(nums) {
    var lines = [];
    for (var i = 0; i < nums.length; i++) {
        lines.push($("#f"+nums[i]).text()); 
    }
    return lines; 
}
function getChecked() {
    return $('input:checkbox:checked').map(function() {
        return this.name;
    }).get();
}
function errmsg(msg) {
    $("#errmsg").text(msg);
}
