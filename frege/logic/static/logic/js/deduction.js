/*
 * functions for handling natural deduction for propositional and predicate logic
 */

// ==========================
// constants
// ==========================

var NEG = '~'; // @@export
var CON = '·'; // @@export
var DIS = '∨'; // @@export
var IMP = '⊃'; // @@export
var EQV = '≡'; // @@export

// ==========================
// deduction state
// ==========================

// holds starting positions of open nestings
var nestingStack = [];
// holds nesting levels by row numbers, only when level changes
var nestingLevels = [];
var lastNestingStart = null;
var rownum = 0; // @@export

initState();

function initState() { // @@export
    nestingStack = [];
    nestingLevels = [];
    nestingLevels[0] = 0;
    lastNestingStart = null;
}

function currentNesting() { // @@export
    return nestingStack.length;
}

function currentNestingStart() {
    return parseInt(nestingStack[nestingStack.length-1]);
}

function endNesting() { // @@export
    endNestingRow();
    lastNestingStart = parseInt(nestingStack.pop());
    updateNesting();
}

function startNesting() { // @@export
    nestingStack.push(rownum+1);
    updateNesting();
}

function updateNesting() {
    nestingLevels[rownum+1] = currentNesting();
}

function isOpenNested(row) { // @@export
    return nestingStack.length > 0 && parseInt(row) >= nestingStack[0];
}

// return true iff the given row is on the current open nesting level
function isOnCurrentLevel(row) { // @@export
    var currLevel = currentNesting();
    if (currLevel === getNesting(row)) {
        // levels are equal, but are the same only in the following case
        return currLevel === 0 || isOpenNested(row);
    } 
    return false;
}

// get the nesting level of row n
function getNesting(n) { // @@export
    n = parseInt(n);
    var startRow = 0;
    for (row in nestingLevels) {
        row = parseInt(row);
        if (row > startRow && row <= n) {
            startRow = row; 
        }
    }
    return nestingLevels[startRow];
}

// ==========================
// deduction rules
// ==========================

// implication elimination
// A⊃B,A => B
function impE(f1, f2) { // @@export
    var a1 = analyze(f1);
    var a2 = analyze(f2);
    var result = _impE(a1, a2);
    if (result) return result;
    return _impE(a2, a1);
}
function _impE(a1, a2) {
    if (a1.con === IMP && equal(a1.sf1, a2.lit)) {
        return stripBrackets(a1.sf2);
    }
}

// conjunction elimination
// A·B => A,B
function conE(f) { // @@export
    var a = analyze(f);
    if (a.con === CON) {
        return [stripBrackets(a.sf1), stripBrackets(a.sf2)];
    }
}

// disjunction elimination
// A∨B,A⊃C,B⊃C => C
function disE(f1, f2, f3) { // @@export
    var a1 = analyze(f1);
    var a2 = analyze(f2);
    var a3 = analyze(f3);
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
    if (equal(aImp1.sf2, aImp2.sf2)) {
        if ((equal(aDis.sf1, aImp1.sf1) && equal(aDis.sf2, aImp2.sf1)) ||
            (equal(aDis.sf1, aImp2.sf1) && equal(aDis.sf2, aImp1.sf1))) {
            return stripBrackets(aImp1.sf2);
        }
    }
}

// equivalence elimination
// A≡B => A⊃B,B⊃A
function eqvE(f) { // @@export
    var a = analyze(f);
    if (a.con === EQV) {
        return [
            a.sf1 + IMP + a.sf2,
            a.sf2 + IMP + a.sf1
        ];
    }
}

// negation elimination
// ~~A => A
function negE(f) { // @@export
    var a = analyze(f);
    if (a.con === NEG) {
        var a2 = analyze(a.sf1);
        if (a2.con === NEG) {
            return stripBrackets(a2.sf1);
        }
    }
}

// implication introduction
// A ... B => A⊃B
function impI() { // @@export
    if (currentNesting() > 0) {
        var formulas = getFormulas([currentNestingStart(), rownum]);
        endNesting();
        return wrap(formulas[0])+IMP+wrap(formulas[1]);
    }
}

// conjunction introduction
// A,B => A·B
function conI(f1, f2) { // @@export
    return wrap(f1)+CON+wrap(f2);
}

// disjunction introduction
// A => A∨B
function disI(f1, f2) { // @@export
    return wrap(f1)+DIS+wrap(f2);
}

// equivalence introduction
// A⊃B,B⊃A => A≡B 
function eqvI(f1, f2) { // @@export
    var a1 = analyze(f1);
    var a2 = analyze(f2);
    if (a1.con === IMP && a2.con === IMP && equal(a1.sf1, a2.sf2) && equal(a1.sf2, a2.sf1)) {
        return a1.sf1 + EQV + a1.sf2;
    }
}

// implication introduction
// A ... B·~B => ~A
function negI() { // @@export
    if (currentNesting() > 0) {
        var formulas = getFormulas([currentNestingStart(), rownum]);
        if (isContradiction(formulas[1])) {
            endNesting();
            return NEG + wrap(formulas[0]);
        }
    }
}

// hypothesis
function hyp(f) { // @@export
    startNesting();
    return f;
}

// repetition
function rep(f) { // @@export
    return f;
}

// ==========================
// formula utils
// ==========================

// check if a formula is syntactically valid
function validate(f) {
    var result = {
        valid: false,
        lit: '',
        err: ''
    };
    var _f = form(f);
    if (isAtomic(_f)) {
        result.valid = true;
        result.lit = _f;
    } else {
        var a = analyze(_f);
        if (a.con == '') {
            result.valid = false;
            result.err = a.err;
        } else {
            result.valid = true;
            result.lit = a.lit;
        }
    }
    return result;
}

// check that a sub formula is syntactically valid
function validateSub(f) {
    // the brackets part checks that the sub formula is surrounded with brackets
    return isAtomic(f) || !isBinary(analyze(f).con) || f !== stripBrackets(f); 
}
// check if a formula is atomic
function isAtomic(f) {
    return f.length === 1 && f === f.toLowerCase() && f.toLowerCase() !== f.toUpperCase();
}

// check if a formula is a contradiction of the form A·~A
function isContradiction(f) { // @@export
    var a = analyze(f);
    if (a.con === CON) {
        var asf1 = analyze(a.sf1);
        var asf2 = analyze(a.sf2);
        return isNegationOf(asf1, asf2) || isNegationOf(asf2, asf1);
    }
    return false;
}

// return true iff one formula is the negation of the other
function isNegationOf(af1, af2) { // @@export
    return af1.con === NEG && equal(af1.sf1, af2.lit);
}

// return true iff both formulas are equal, up to commutativity and brackets ommission
function equal(f1, f2) { // @@export
    var a1 = analyze(f1);
    var a2 = analyze(f2);
    if (a1.lit === a2.lit) return true;
    if (isAtomic(f1)) return false;
    if (a1.con === a2.con) {
        if (equal(a1.sf1, a2.sf1) && equal(a1.sf2, a2.sf2)) return true;
        if (isCommutative(a1.con)) {
            return equal(a1.sf1, a2.sf2) && equal(a1.sf2, a2.sf1);
        }
    }
    return false;
}

// return the main connective and sub formula(s) of a formula
function analyze(f) { // @@export
    var _f = form(f);
    var result = {
        lit: _f,
        con: '',
        sf1: '',
        sf2: ''
    };
    if (isAtomic(_f)) return result;
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
                var next = _f.charAt(i+1);
                if (!(isAtomic(next) || next === NEG || next === '(')) {
                    result.err = generr;
                    return result;
                }
            }
        } else if (nesting === 0) {
            // highest nesting level, check for main connective
            if (isBinary(c)) {
                var sf1 = _f.slice(0, i);
                var sf2 = _f.slice(i+1);
                if (!validateSub(sf1) || !validateSub(sf2) || !validate(sf1).valid || !validate(sf2).valid) {
                    result.err = generr;
                    return result;
                }
                result.con = c;
                result.sf1 = sf1; 
                result.sf2 = sf2; 
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
        var sf = _f.slice(1);
        if (_f.charAt(0) !== NEG || !validate(sf).valid) {
            result.err = generr;
            return result;
        } 
        result.con = NEG;
        result.sf1 = sf;
        return result;
    }
    result.err = generr;
    return result;
}

// strip brackets and remove spaces from a formula string
function form(f) {
    return stripBrackets(f).replace(/ /g,'');
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

function isBinary(c) {
    return c === CON || c === DIS || c === IMP || c === EQV;
}

function isCommutative(c) {
    return c === CON || c === DIS || c === EQV;
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
var okTxt = 'OK';

// perform handling before applying rule
function doApply(btn, func, num, symFunc, withText, isRep) {
    lastBtn = null;
    if (withText) {
        if (btn.text() === okTxt) {
            if (applyRule(func, num, symFunc, withText, isRep)) {
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
        applyRule(func, num, symFunc, withText, isRep);
    }
    btn.blur();
}

// general function for applying a rule, gets rule-specific parameters and callbacks
function applyRule(ruleFunc, numRows, symbolFunc, withText, isRep) {
    if (!validateSelection(numRows, isRep)) {
        return;
    }
    var checked = getChecked();
    var formulas = getFormulas(checked); 
    if (withText) {
        var text = getText();
        if (!text) {
            return errmsg("יש להזין נוסחה");
        }
        var result = validate(text);
        if (!result.valid) {
            return errmsg(result.err);
        }
        formulas.push(result.lit);
    }
    // apply the rule
    var consq = ruleFunc.apply(this, formulas);
    if (consq) {
        var symbol = symbolFunc(checked);
        // add the new row(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (var i = 0; i < consq.length; i++) {
            addRow(consq[i], symbol);
        }
        removeSelection();
        $.notifyClose();
        return true;
    } else {
        if (numRows > 0 ) {
            return errmsg("לא ניתן להשתמש בכלל זה עבור השורות שנבחרו");
        }
        return errmsg("לא ניתן להשתמש בכלל זה במצב הנוכחי");
    }
}

function removeSelection() {
    $("input[type=checkbox]").prop("checked", false);
}

// return true if user selection is ok, otherwise print error and return false
function validateSelection(numRows, isRep) {
    if (numRows > 0) {
        var checked = getChecked();
        if (checked.length != numRows) {
            var words = ["", "שורה אחת", "שתי שורות", "שלוש שורות"];
            errmsg("יש לבחור "+words[numRows]+" בדיוק על מנת להשתמש בכלל זה");
            return false;
        }
        if (isRep) return validateRep(checked);
        for (var i = 0; i < checked.length; i++) {
            if (!isOnCurrentLevel(checked[i])) {
                errmsg("שורה " + checked[i] + " מחוץ לרמה הנוכחית");
                return false;
            }
        }
    } else {
        removeSelection();
    }
    return true;
}

// check that the selected row can be repeated
function validateRep(checked) {
    var n = checked[0];
    if (isOnCurrentLevel(n)) {
        errmsg("שורה " + n + " כבר נמצאת ברמה הנוכחית");
        return false;
    }
    if (getNesting(n) > 0 && !isOpenNested(n)) {
        errmsg("שורה " + n + " נמצאת בתת הוכחה אחרת");
        return false;
    }
    return true;
}

// add a new row to the deduction table
function addRow(content, symbol, premise) {
    rownum++;
    if (premise) {
        var rowId = '';
        symbol = 'prem';
    } else {
       var rowId = 'r'+rownum;
    }
    // handle nesting
    for (var i = 0; i < currentNesting(); i++) content = addNesting(content, rownum, currentNesting() - i);
    // add the row
    $('#deduction tr:last').after(
        '<tr id="'+rowId+'">'+
          '<td class="dd-num""><input type="checkbox" id="cb'+rownum+'" name="'+rownum+'" onclick="oncheck()">'+rownum+'. </input></td>'+
          '<td id="f'+rownum+'">'+content+'</td>'+
          '<td class="dd-just">'+symbol+'</td>'+
        '</tr>'
    );
}

// remove the last deduction row 
function removeRow() {
    removeSelection();
    // delete by row id (premises don't have row id and so cannot be deleted)
    $("#r"+rownum).remove();
    rownum--;
}

// add a nesting indication to given html
function addNesting(content, row, level) {
    return '<div class="dd-hyp" id="nst'+row+''+level+'">'+content+'</div>';
}

// add a end of nesting indication
function endNestingRow() {
    $("#nst"+rownum+""+currentNesting()).addClass("dd-hyp-end");
}

// symbol functions
function symbolImpE(rows) {
    return "E ⊃ " + rows[0] + "," + rows[1];
}
function symbolConE(rows) {
    return "E · " + rows[0];
}
function symbolDisE(rows) {
    return "E ∨ " + rows[0] + "," + rows[1] + "," + rows[2];
}
function symbolEqvE(rows) {
    return "E ≡ " + rows[0];
}
function symbolNegE(rows) {
    return "E ~ " + rows[0];
}
function symbolImpI() {
    return "I ⊃ " + lastNestingStart + "-" + rownum;
}
function symbolConI(rows) {
    return "I · " + rows[0] + "," + rows[1];
}
function symbolDisI(rows) {
    return "I ∨ " + rows[0];
}
function symbolEqvI(rows) {
    return "I ≡ " + rows[0] + "," + rows[1];
}
function symbolNegI() {
    return "I ~ " + lastNestingStart + "-" + rownum;
}
function symbolHyp() {
    return "hyp";
}
function symbolRep(rows) {
    return "rep " + rows[0];
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
    $.notify({
        message: msg
    },{
        allow_dismiss: true,
        delay: 1400,
	template:
          '<div data-notify="container" class="col-xs-11 col-sm-3 alert text-center note" role="alert">' +
            '<span data-notify="dismiss">' + 
              '<span data-notify="message">{2}</span>' +
            '</span>' +
          '</div>'
    });
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
        btn.text(okTxt);
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
    hideText(lastBtn);
}

// @@skipstart
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

// bind rule buttons to functions and symbol buttons to insertions
$(document).ready(function() {
    $("#imp-e").click(function() {
        doApply($(this), impE, 2, symbolImpE);
    });
    $("#con-e").click(function() {
        doApply($(this), conE, 1, symbolConE);
    });
    $("#dis-e").click(function() {
        doApply($(this), disE, 3, symbolDisE);
    });
    $("#eqv-e").click(function() {
        doApply($(this), eqvE, 1, symbolEqvE);
    });
    $("#neg-e").click(function() {
        doApply($(this), negE, 1, symbolNegE);
    });
    $("#imp-i").click(function() {
        doApply($(this), impI, 0, symbolImpI);
    });
    $("#con-i").click(function() {
        doApply($(this), conI, 2, symbolConI);
    });
    $("#dis-i").click(function() {
        doApply($(this), disI, 1, symbolDisI, true);
    });
    $("#eqv-i").click(function() {
        doApply($(this), eqvI, 2, symbolEqvI);
    });
    $("#neg-i").click(function() {
        doApply($(this), negI, 0, symbolNegI);
    });
    $("#hyp").click(function() {
        doApply($(this), hyp, 0, symbolHyp, true);
    });
    $("#rep").click(function() {
        doApply($(this), rep, 1, symbolRep, false, true);
    });
    $("#rem").click(function() {
        removeRow();
        $(this).blur();
    });
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
// @@skipend
