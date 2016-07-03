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
// deduction state
// ==========================

// holds starting positions of open nestings
var nestingStack = [];
var lastNestingStart = null;

function currentNesting() {
    return nestingStack.length;
}

function currentNestingStart() {
    return nestingStack[nestingStack.length-1];
}

function endNesting() {
    lastNestingStart = nestingStack.pop();
}

function startNesting() {
    nestingStack.push(nextLineNumber());
}

function isOpenNested(lineNum) {
    return nestingStack.length > 0 && lineNum > nestingStack[0];
}

// ==========================
// deduction rules
// ==========================

// implication elimination
// A⊃B,A => B
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
// A·B => A,B
function conE(f) {
    a = analyze(f);
    if (a.con === CON) {
        return [stripBrackets(a.sf1), stripBrackets(a.sf2)];
    }
}

// disjunction elimination
// A∨B,A⊃C,B⊃C => C
function disE(f1, f2, f3) {
    a1 = analyze(f1);
    a2 = analyze(f2);
    a3 = analyze(f3);
    if (a1.con === DIS && a2.con === IMP && a3.con === IMP) {
        return _disE(a1, a2, a3);
    }
    if (a2.con === DIS && a1.con === IMP && a3.con === IMP) {
        return _disE(a2, a1, a3);
    }
    if (a3.con === DIS && a2.con === IMP && a1.con === IMP) {
        return _disE(a3, a2, a1);
    }
}
function _disE(aDis, aImp1, aImp2) {
    if (aImp1.sf2 === aImp2.sf2) {
        if ((aDis.sf1 === aImp1.sf1 && aDis.sf2 === aImp2.sf1) || (aDis.sf1 === aImp2.sf1 && aDis.sf2 === aImp1.sf1)) {
            return stripBrackets(aImp1.sf2);
        }
    }
}

// negation elimination
// ~~A => A
function negE(f) {
    a = analyze(f);
    if (a.con === NEG) {
        a2 = analyze(a.sf1);
        if (a2.con === NEG) {
            return stripBrackets(a2.sf1);
        }
    }
}

// implication introduction
// A ... B => A⊃B
function impI() {
    if (currentNesting() > 0) {
        formulas = getFormulas([currentNestingStart(), currentLineNumber()]);
        endNesting();
        return wrap(formulas[0])+IMP+wrap(formulas[1]);
    }
}

// conjunction introduction
// A,B => A·B
function conI(f1, f2) {
    return wrap(f1)+CON+wrap(f2);
}

// disjunction introduction
// A => A∨B
function disI(f1, f2) {
    return wrap(f1)+DIS+wrap(f2);
}

// hypothesis
function hyp(f) {
    startNesting();
    return f;
}

// ==========================
// formula utils
// ==========================

// check if a formula is syntactically valid
function validate(f) {
    var result = {
        valid: false,
        literal: '',
        err: ''
    };
    var _f = stripBrackets(f).replace(/ /g,'');
    if (isAtomic(_f)) {
        result.valid = true;
        result.literal = _f;
    } else {
        a = analyze(_f);
        if (a.con == '') {
            result.valid = false;
            result.err = a.err;
        } else {
            result.valid = true;
            result.literal = a.lit;
        }
    }
    return result;
}

// check that a sub formula is syntactically valid
function validateSub(f) {
    // the brackets part checks that the sub formula is surrounded with brackets
    return isAtomic(f) || (f !== stripBrackets(f)); 
}
// check if a formula is atomic
function isAtomic(f) {
    return f.length === 1 && f === f.toLowerCase() && f.toLowerCase() !== f.toUpperCase();
}

// return the main connective and sub formula(s) of a formula
function analyze(f) {
    var _f = stripBrackets(f).replace(/ /g,'');
    var result = {
        lit: _f,
        con: '',
        sf1: '',
        sf2: ''
    };
    var generr = 'נוסחה לא תקינה';
    var maybe_neg = false;
    var nesting = 0;
    for (var i = 0; i < _f.length; i++) {
        var c = _f.charAt(i);
        if (c === ')') {
            nesting--;
        } else if (c === '(') {
            nesting++;
            // validate next char
            if (i+1 < _f.length) {
                next = _f.charAt(i+1);
                if (!(isAtomic(next) || next === NEG || next === '(')) {
                    result.err = generr;
                    return result;
                }
            }
        } else if (nesting === 0) {
            // highest nesting level, check for main connective
            if (c === CON || c === DIS || c === IMP || c === EQV) {
                sf1 = _f.slice(0, i);
                sf2 = _f.slice(i+1);
                if (!validateSub(sf1) || !validateSub(sf2) || !validate(sf1).valid || !validate(sf2).valid) {
                    result.err = generr;
                    return result;
                }
                result.con = c;
                result.sf1 = _f.slice(0, i); // dont use sf1, it's overwritten TODO: can probably use it with `var`
                result.sf2 = _f.slice(i+1); // same
                return result;
            } else if (c === NEG) {
                // don't return here since binary connectives take precedence
                maybe_neg = true;
            }
        } else if (nesting < 0) {
            result.err = 'סוגריים לא מאוזנים';
            return result;
        }
    }
    if (nesting !== 0) {
        result.err = 'סוגריים לא מאוזנים';
        return result;
    }
    if (maybe_neg) {
        // validate negation
        sf = _f.slice(1);
        if (_f.charAt(0) !== NEG || !validate(sf).valid) {
            result.err = generr;
            return result;
        } 
        result.con = NEG;
        result.sf1 = _f.slice(1); // dont use sf, it's overwritten
        return result;
    }
    result.err = generr;
    return result;
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
    if (f.length > 1 && analyze(f).con != NEG) {
        return '('+f+')';
    }
    return f;
}

// ==========================
// user interaction
// ==========================

var lastBtn = null;

// perform handling before applying rule
function doApply(btn, func, num, symFunc, withText) {
    lastBtn = null;
    if (withText) {
        if (btn.text() === "OK") {
            if (applyRule(func, num, symFunc, withText)) {
                hideText(btn);
            }
        } else {
            hideText(btn);
            if (validateSelection(num)) {
                showText(btn);
                lastBtn = btn;
            }
        }
    } else {
        applyRule(func, num, symFunc, withText);
    }
    btn.blur();
}

// general function for applying a rule, gets rule-specific parameters and callbacks
function applyRule(ruleFunc, numLines, symbolFunc, withText) {
    errmsg("");
    if (!validateSelection(numLines)) {
        return;
    }
    checked = getChecked();
    formulas = getFormulas(checked); 
    if (withText) {
        text = getText();
        if (!text) {
            return errmsg("יש להזין נוסחה");
        }
        result = validate(text);
        if (!result.valid) {
            return errmsg(result.err);
        }
        formulas.push(result.literal);
    }
    // apply the rule
    consq = ruleFunc.apply(this, formulas);
    if (consq) {
        // get new line number
        var n = nextLineNumber();
        var symbol = symbolFunc(checked);
        // add the new line(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (i = 0; i < consq.length; i++) {
            addLine(n+i, consq[i], symbol);
        }
        removeSelection();
        return true;
    } else {
        if (numLines > 0 ) {
            return errmsg("לא ניתן להשתמש בכלל עבור השורות שנבחרו");
        }
        return errmsg("לא ניתן להשתמש בכלל במצב זה");
    }
}

function currentLineNumber() {
    return $("#deduction >tbody >tr").length;
}
function nextLineNumber() {
    return currentLineNumber() + 1;
}

function removeSelection() {
    $("input[type=checkbox]").prop("checked", false);
}

function validateSelection(numLines) {
    errmsg("");
    if (numLines > 0) {
        checked = getChecked();
        if (checked.length != numLines) {
            words = ["", "שורה אחת", "שתי שורות", "שלוש שורות"];
            errmsg("יש לבחור "+words[numLines]+" בדיוק על מנת להשתמש בכלל זה");
            return false;
        }
    } else {
        removeSelection();
    }
    return true;
}

// add a deduction line with number and symbol
function addLine(n, content, symbol) {
    for (i = 0; i < currentNesting(); i++) content = addNesting(content);
    $('#deduction tr:last').after(
        '<tr>'+
          '<td class="dd-num""><input type="checkbox" id="cb'+n+'" name="'+n+'" onclick="oncheck()">'+n+'. </input></td>'+
          '<td id="f'+n+'">'+content+'</td>'+
          '<td class="dd-just">'+symbol+'</td>'+
        '</tr>'
    );
}

// add a nesting indication to given html
function addNesting(content) {
    return '<div class="dd-hyp">'+content+'</div>';
}

// symbol functions
function symbolImpE(lineNums) {
    return "E ⊃ " + lineNums[0] + "," + lineNums[1];
}
function symbolConE(lineNums) {
    return "E · " + lineNums[0];
}
function symbolDisE(lineNums) {
    return "E ∨ " + lineNums[0] + "," + lineNums[1] + "," + lineNums[2];
}
function symbolNegE(lineNums) {
    return "E ~ " + lineNums[0];
}
function symbolImpI() {
    return "I ⊃ " + lastNestingStart + "-" + currentLineNumber();
}
function symbolConI(lineNums) {
    return "I · " + lineNums[0] + "," + lineNums[1];
}
function symbolDisI(lineNums) {
    return "I ∨ " + lineNums[0];
}
function symbolHyp() {
    return "hyp";
}

// utils
function getFormulas(nums) {
    var formulas = [];
    for (var i = 0; i < nums.length; i++) {
        formulas.push($("#f"+nums[i]).text()); 
    }
    return formulas; 
}
function getChecked() {
    return $('input:checkbox:checked').map(function() {
        return this.name;
    }).get();
}
function errmsg(msg) {
    $("#errmsg").text(msg);
}
function showText(btn) {
    $("#extra").css("opacity","1");
    setTimeout(function(){ // trick to not miss the focus
        $("#extxt").focus();
    }, 5);
    $("#extxt").on("input", function() {
        if (!btn.data("symbol")) {
            // save button symbol before replacing
            btn.data("symbol", btn.text());
        }
        btn.removeClass("btn-default");
        btn.addClass("btn-primary");
        btn.text("OK");
    });
    $(document).keypress(function(e) {
        if (e.which == 13) { // Enter 
            btn.click();
        }
    });
}
function hideText(btn) {
    $("#extra").css("opacity","0");
    $("#extxt").val("");
    $("#extxt").off("input");
    $(document).off("keypress");
    if (btn) {
        // restore button defaults
        btn.addClass("btn-default");
        btn.removeClass("btn-primary");
        btn.text(btn.data("symbol"));
    }
}
function getText() {
    return $("#extxt").val();
}

// checkbox click handler
function oncheck() {
    errmsg("");
    hideText(lastBtn);
}

// function for inserting text at cursor position
jQuery.fn.extend({
    insertAtCaret: function(myValue){
        return this.each(function(i) {
            if (document.selection) {
                //For browsers like Internet Explorer
                this.focus();
                var sel = document.selection.createRange();
                sel.text = myValue;
                this.focus();
            } else if (this.selectionStart || this.selectionStart == '0') {
                //For browsers like Firefox and Webkit based
                var startPos = this.selectionStart;
                var endPos = this.selectionEnd;
                var scrollTop = this.scrollTop;
                this.value = this.value.substring(0, startPos)+myValue+this.value.substring(endPos,this.value.length);
                this.focus();
                this.selectionStart = startPos + myValue.length;
                this.selectionEnd = startPos + myValue.length;
                this.scrollTop = scrollTop;
            } else {
                this.value += myValue;
                this.focus();
            }
        });
    }
});
function insert(text) {
    $("#extxt").insertAtCaret(text);
    $("#extxt").focus();
}

// bind symbol buttons to insertions
$(document).ready(function() {
    $("#neg").click(function() {
        insert('~');
    });
    $("#con").click(function() {
        insert('·');
    });
    $("#dis").click(function() {
        insert('∨');
    });
    $("#imp").click(function() {
        insert('⊃');
    });
    $("#eqv").click(function() {
        insert('≡');
    })
});
