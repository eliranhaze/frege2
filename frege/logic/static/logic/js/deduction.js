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
// formula 
// ==========================

// formula constructor
function Formula(f, opts) { // @@export
    this.con = null;
    this.sf1 = null;
    this.sf2 = null;
    this.lit = form(f);
    this.analyze(this.lit);
}

// find the main connective and sub formula(s) of a formula
Formula.prototype.analyze = function(f) {
    if (this.isAtomic()) return;
    var generr = 'נוסחה לא תקינה';
    var maybe_neg = false;
    var nesting = 0;
    for (var i = 0; i < f.length; i++) {
        var c = f.charAt(i);
        if (c == ')') {
            nesting--;
        } else if (c == '(') {
            nesting++;
            // validate next char
            if (i+1 < f.length) {
                var next = f.charAt(i+1);
                if (!(isAlpha(next) || next == NEG || next == '(')) {
                    throw new Error(generr);
                }
            }
        } else if (nesting === 0) {
            // highest nesting level, check for main connective
            if (isBinary(c)) {
                var _sf1 = f.slice(0, i);
                var _sf2 = f.slice(i+1);
                this.con = c;
                this.sf1 = new Formula(_sf1); 
                this.sf2 = new Formula(_sf2); 
                if (!this.sf1.validateSub(_sf1) || !this.sf2.validateSub(_sf2)) {
                    throw new Error(generr);
                }
                return;
            } else if (c === NEG) {
                // don't return here since binary connectives take precedence
                maybe_neg = true;
            }
        } else if (nesting < 0) {
            throw new Error('סוגריים לא מאוזנים');
        }
    }
    if (nesting !== 0) {
        throw new Error('סוגריים לא מאוזנים');
    }
    if (maybe_neg) {
        // validate negation
        var sf = f.slice(1);
        if (f.charAt(0) !== NEG) {
            throw new Error(generr);
        } 
        this.con = NEG;
        this.sf1 = new Formula(sf);
        return;
    }
    throw new Error(generr);
}

Formula.prototype.isAtomic = function() {
    return this.lit.length == 1 && isAlpha(this.lit);
}

// check if a formula is a contradiction of the form A·~A
Formula.prototype.isContradiction = function() {
    if (this.con === CON) {
        return this.sf1.isNegationOf(this.sf2) || this.sf2.isNegationOf(this.sf1);
    }
    return false;
}

Formula.prototype.isNegationOf = function(other) {
    return this.con === NEG && this.sf1.equals(other);
}

// return true iff both formulas are equal, up to commutativity and brackets ommission
Formula.prototype.equals = function(other) {
    if (!other) return false;
    if (this.lit == other.lit) return true;
    if (this.isAtomic()) return false;
    if (this.con == other.con) {
        if (!isBinary(this.con)) return this.sf1.equals(other.sf1);
        if (this.sf1.equals(other.sf1) && this.sf2.equals(other.sf2)) return true;
        if (isCommutative(this.con)) {
            return this.sf1.equals(other.sf2) && this.sf2.equals(other.sf1);
        }
    }
    return false;
}

// combine this and another formula using a binary connective
// returns a new formula
Formula.prototype.combine = function(other, c) {
    if (isBinary(c)) {
        f = new Formula('p'); // this is a bit of a hack    
        f.con = c;
        f.sf1 = this;
        f.sf2 = other;
        f.lit = this.wrap() + c + other.wrap();
        return f;
    }
}

// return a negation of this formula
Formula.prototype.negate = function() {
    f = new Formula('p');    
    f.con = NEG;
    f.sf1 = this;
    f.lit = NEG + this.wrap();
    return f;
}
// wrap a formula with brackets if needed, returns a string
Formula.prototype.wrap = function() {
    if (isBinary(this.con)) {
        return '('+this.lit+')';
    }
    return this.lit;
}

// check that a sub formula is syntactically valid
Formula.prototype.validateSub = function(original) {
    // the brackets part checks that the sub formula is surrounded with brackets
    return this.isAtomic() || !isBinary(this.con) || original !== stripBrackets(original); 
}

Formula.prototype.toString = function() {
    return this.lit;
}

// ==========================
// formula utils
// ==========================

function isAlpha(a) {
    return a.toLowerCase() != a.toUpperCase();
}

function isBinary(c) {
    return c === CON || c === DIS || c === IMP || c === EQV;
}

function isCommutative(c) {
    return c === CON || c === DIS || c === EQV;
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

// ==========================
// deduction
// ==========================

// deduction constructor
function Deduction() { // @@export
    this.formulas = [null]; // 1-indexed
    this.nestingLevels = [0];
    this.nestingStack = [];
    this.reverseStack = [];
    this.lastSymbol = '';
}

// return the current index (1-indexed)
Deduction.prototype.index = function() {
    return this.formulas.length - 1;
}

// return the current nesting level
Deduction.prototype.nesting = function() {
    return this.nestingStack.length;
}

// return the index at which the current nesting was opened
Deduction.prototype.openIndex = function() {
    return this.nestingStack[this.nestingStack.length - 1];
}

// add a formula to the deduction
Deduction.prototype.push = function(f, nest, endnest) {
    this.formulas.push(f);
    if (nest) this.nestingStack.push(this.index());
    else if (endnest) {
        // save the popped item in case of going back
        this.reverseStack.push(this.nestingStack.pop());
    }
    this.nestingLevels.push(this.nesting());
}

// remove the last formula from the deduction
Deduction.prototype.pop = function() {
    if (this.index() == 0) return;
    var prevNesting = this.nesting();
    var prevIndex = this.index();
    this.formulas.pop();
    this.nestingLevels.pop();
    // handle nesting change
    if (this.nestingLevels[this.index()] != prevNesting) {
        if (this.openIndex() == prevIndex) {
            // going down
            this.nestingStack.pop();
        } else {
            // going up
            this.nestingStack.push(this.reverseStack.pop());
        }
    }
}

// return true iff the given row is on some open nesting
Deduction.prototype.isOpenNested = function(i) {
    var iLvl = this.nestingLevels[i];
    if (iLvl > 0 && iLvl <= this.nesting()) {
        var iOpenIndex = this.nestingStack[iLvl-1]; 
        return i >= iOpenIndex;
    }
    return false;
}

// return true iff the given row is on the current open nesting level
Deduction.prototype.isOnCurrentLevel = function(i) {
    var currLevel = this.nesting();
    if (currLevel == this.nestingLevels[i]) {
        // levels are equal, but are the same only in the following case
        return currLevel == 0 || this.isOpenNested(i);
    } 
    return false;
}

Deduction.prototype.getFormula = function(i) {
    if (i > 0 && i <= this.index()) return this.formulas[i];
}

Deduction.prototype.toString = function() {
    var s = '';
    for (var i = 1; i < this.formulas.length; i++) {
        s += '[' + this.nestingLevels[i] + '] ' + i + '. ' + this.formulas[i] + '\n';
    }
    return s;
}

// ==========================
// deduction rules
// ==========================

// implication elimination
// A⊃B,A => B
Deduction.prototype.impE = function(i1, i2) {
    if (!this.isOnCurrentLevel(i1) || !this.isOnCurrentLevel(i2)) return;
    _impE = function(imp, ant) {
        if (imp && imp.con == IMP && imp.sf1.equals(ant)) return imp.sf2;
    }
    var f1 = this.getFormula(i1);
    var f2 = this.getFormula(i2);
    var result = _impE(f1, f2);
    if (!result) result = _impE(f2, f1);
    if (result) {
        this.lastSymbol = 'E ' + IMP + ' ' + i1 + ',' + i2;
        this.push(result);
        return result;
    }
}

// conjunction elimination
// A·B => A,B
Deduction.prototype.conE = function(i) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.getFormula(i);
    if (f && f.con == CON) {
        var result = [f.sf1, f.sf2];
        this.lastSymbol = 'E ' + CON + ' ' + i;
        this.push(result[0]);
        this.push(result[1]);
        return result;
    }
}

// disjunction elimination
// A∨B,A⊃C,B⊃C => C
Deduction.prototype.disE = function(i1, i2, i3) {
    if (!this.isOnCurrentLevel(i1) || !this.isOnCurrentLevel(i2) || !this.isOnCurrentLevel(i3)) return;
    _disE = function(dis, imp1, imp2) {
        if (imp1.sf2.equals(imp2.sf2)) {
            if (dis.equals(imp1.sf1.combine(imp2.sf1, DIS))) return imp1.sf2;
        }
    }
    var f1 = this.getFormula(i1);
    var f2 = this.getFormula(i2);
    var f3 = this.getFormula(i3);
    var result = null;
    if (!f1 || !f2 || !f3) return;
    if (f1.con == DIS && f2.con == IMP && f3.con == IMP) {
        result = _disE(f1, f2, f3);
    } else if (f2.con == DIS && f1.con == IMP && f3.con == IMP) {
        result = _disE(f2, f1, f3);
    } else if (f3.con == DIS && f2.con == IMP && f1.con == IMP) {
        result = _disE(f3, f2, f1);
    } else return;
    this.lastSymbol = 'E ' + DIS + ' ' + i1 + ',' + i2 + ',' + i3;
    this.push(result);
    return result;
}

// equivalence elimination
// A≡B => A⊃B,B⊃A
Deduction.prototype.eqvE = function(i) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.getFormula(i);
    if (f && f.con == EQV) {
        var result = [
            f.sf1.combine(f.sf2, IMP),
            f.sf2.combine(f.sf1, IMP),
        ];
        this.lastSymbol = 'E ' + EQV + ' ' + i;
        this.push(result[0]);
        this.push(result[1]);
        return result;
    }
}

// negation elimination
// ~~A => A
Deduction.prototype.negE = function(i) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.getFormula(i);
    if (f && f.con == NEG && f.sf1.con == NEG) {
        var result = f.sf1.sf1;
        this.lastSymbol = 'E ' + NEG + ' ' + i;
        this.push(result);
        return result;
    }
}

// conjunction introduction
// A,B => A·B
Deduction.prototype.conI = function(i1, i2) {
    if (!this.isOnCurrentLevel(i1) || !this.isOnCurrentLevel(i2)) return;
    var f1 = this.getFormula(i1);
    var f2 = this.getFormula(i2);
    if (f1 && f2) {
        var result = f1.combine(f2, CON);
        this.lastSymbol = 'I ' + CON + ' ' + i1 + ',' + i2;
        this.push(result);
        return result;
    }
}

// disjunction introduction
// A => A∨B
Deduction.prototype.disI = function(i1, f2) {
    if (!this.isOnCurrentLevel(i1)) return;
    var f1 = this.getFormula(i1);
    if (f1 && f2) {
        var result = f1.combine(f2, DIS);
        this.lastSymbol = 'I ' + DIS + ' ' + i1;
        this.push(result);
        return result;
    }
}

// equivalence introduction
// A⊃B,B⊃A => A≡B 
Deduction.prototype.eqvI = function(i1, i2) {
    if (!this.isOnCurrentLevel(i1) || !this.isOnCurrentLevel(i2)) return;
    var f1 = this.getFormula(i1);
    var f2 = this.getFormula(i2);
    if (f1 && f2 && f1.con == IMP && f2.con == IMP &&
        f1.sf1.equals(f2.sf2) && f2.sf1.equals(f1.sf2)) {
        var result = f1.sf1.combine(f1.sf2, EQV);
        this.lastSymbol = 'I ' + EQV + ' ' + i1 + ',' + i2;
        this.push(result);
        return result;
    }
}

// implication introduction
// A ... B => A⊃B
Deduction.prototype.impI = function() {
    if (this.nesting() > 0) {
        var f1 = this.getFormula(this.openIndex());
        var f2 = this.getFormula(this.index());
        if (f1 && f2) {
            var result = f1.combine(f2, IMP);
            this.lastSymbol = 'I ' + IMP + ' ' + this.openIndex() + '-' + this.index();
            this.push(result, false, true);
            return result;
        }
    }
}

// negation introduction
// A ... B·~B => ~A
Deduction.prototype.negI = function() { // @@export
    if (this.nesting() > 0) {
        var f1 = this.getFormula(this.openIndex());
        var f2 = this.getFormula(this.index());
        if (f1 && f2 && f2.isContradiction()) {
            var result = f1.negate();
            this.lastSymbol = 'I ' + NEG + ' ' + this.openIndex() + '-' + this.index();
            this.push(result, false, true);
            return result;
        }
    }
}

// hypothesis
Deduction.prototype.hyp = function(f) {
    this.lastSymbol = 'hyp';
    this.push(f, true);
    return f;
}
 
// repetition
Deduction.prototype.rep = function(i) {
    var f = this.getFormula(i);
    if (!f) return;
    if (this.isOnCurrentLevel(i)) {
        throw Error("שורה " + i + " כבר נמצאת ברמה הנוכחית");
    }
    if (this.nestingLevels[i] > 0 && !this.isOpenNested(i)) {
        throw Error("שורה " + i + " נמצאת בתת הוכחה אחרת");
    }
    this.lastSymbol = 'rep ' + i;
    this.push(f);
    return f;
}

// ==========================
// user interaction
// ==========================

var deduction = new Deduction();
var lastBtn = null;
var okTxt = 'OK';

// perform handling before applying rule
function doApply(btn, func, num, withText, isRep) {
    lastBtn = null;
    if (withText) {
        if (btn.text() === okTxt) {
            if (applyRule(func, num, withText)) {
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
        applyRule(func, num, withText, isRep);
    }
    btn.blur();
}

// general function for applying a rule, gets rule-specific parameters and callbacks
function applyRule(ruleFunc, numRows, withText, isRep) {
    if (!validateSelection(numRows, isRep)) {
        return;
    }
    var args = getChecked();
    if (withText) {
        var text = getText();
        if (!text) return errmsg("יש להזין נוסחה");
        try { var formula = new Formula(text); }
        catch (e) { return errmsg(e.message); }
        args.push(formula);
    }
    var prevNesting = deduction.nesting();
    // apply the rule
    try {var consq = ruleFunc.apply(deduction, args);}
    catch (e) {return errmsg(e.message);}
    if (consq) {
        // add the new row(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (var i = 0; i < consq.length; i++) {
            addRow(consq[i].lit, deduction.lastSymbol, false, (deduction.index() - consq.length + i + 1));
        }
        if (prevNesting > deduction.nesting()) endNestingLine(deduction.index() - 1, prevNesting);
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
        if (isRep) return true;
        for (var i = 0; i < checked.length; i++) {
            if (!deduction.isOnCurrentLevel(checked[i])) {
                errmsg("שורה " + checked[i] + " מחוץ לרמה הנוכחית");
                return false;
            }
        }
    } else {
        removeSelection();
    }
    return true;
}

// add a new row to the deduction table
function addRow(content, symbol, premise, rownum) {
    if (premise) {
        var rowId = '';
        symbol = 'prem';
        deduction.push(new Formula(content));
        rownum = deduction.index();
    } else {
       var rowId = 'r'+rownum;
    }
    var nesting = deduction.nesting();
    // handle nesting
    for (var i = 0; i < nesting; i++) content = addNesting(content, rownum, nesting - i);
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
    // delete by row id (premises don't have row id and so cannot be deleted)
    var rownum = deduction.index();
    if ($("#r"+rownum).length == 0) return;
    $("#r"+rownum).remove();
    removeSelection();
    var nesting = deduction.nesting();
    deduction.pop();
    if (deduction.nesting() > nesting) endNestingLine(deduction.index(), deduction.nesting());
}

// add a nesting indication to given html
function addNesting(content, row, level) {
    return '<div class="dd-hyp" id="nst'+row+''+level+'">'+content+'</div>';
}

// add a end of nesting indication
function endNestingLine(index, nesting) {
    $("#nst"+index+""+nesting).toggleClass("dd-hyp-end");
}

// utils
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
        offset: {x: 0, y: 200},
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
        doApply($(this), deduction.impE, 2);
    });
    $("#con-e").click(function() {
        doApply($(this), deduction.conE, 1);
    });
    $("#dis-e").click(function() {
        doApply($(this), deduction.disE, 3);
    });
    $("#eqv-e").click(function() {
        doApply($(this), deduction.eqvE, 1);
    });
    $("#neg-e").click(function() {
        doApply($(this), deduction.negE, 1);
    });
    $("#imp-i").click(function() {
        doApply($(this), deduction.impI, 0);
    });
    $("#con-i").click(function() {
        doApply($(this), deduction.conI, 2);
    });
    $("#dis-i").click(function() {
        doApply($(this), deduction.disI, 1, true);
    });
    $("#eqv-i").click(function() {
        doApply($(this), deduction.eqvI, 2);
    });
    $("#neg-i").click(function() {
        doApply($(this), deduction.negI, 0);
    });
    $("#hyp").click(function() {
        doApply($(this), deduction.hyp, 0, true);
    });
    $("#rep").click(function() {
        doApply($(this), deduction.rep, 1, false, true);
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
