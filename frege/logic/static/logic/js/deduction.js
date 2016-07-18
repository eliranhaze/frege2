/*
 * functions for handling natural deduction for propositional and predicate logic
 */

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
Deduction.prototype.idx = function() {
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
    if (nest) this.nestingStack.push(this.idx());
    else if (endnest) {
        // save the popped item in case of going back
        this.reverseStack.push(this.nestingStack.pop());
    }
    this.nestingLevels.push(this.nesting());
}

// remove the last formula from the deduction
Deduction.prototype.pop = function() {
    if (this.idx() == 0) return;
    var prevNesting = this.nesting();
    var prevIndex = this.idx();
    this.formulas.pop();
    this.nestingLevels.pop();
    // handle nesting change
    if (this.nestingLevels[this.idx()] != prevNesting) {
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

Deduction.prototype.get = function(i) {
    if (i > 0 && i <= this.idx()) return this.formulas[i];
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
    var f1 = this.get(i1);
    var f2 = this.get(i2);
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
    var f = this.get(i);
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
    var f1 = this.get(i1);
    var f2 = this.get(i2);
    var f3 = this.get(i3);
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
    var f = this.get(i);
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
    var f = this.get(i);
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
    var f1 = this.get(i1);
    var f2 = this.get(i2);
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
    var f1 = this.get(i1);
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
    var f1 = this.get(i1);
    var f2 = this.get(i2);
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
        var f1 = this.get(this.openIndex());
        var f2 = this.get(this.idx());
        if (f1 && f2) {
            var result = f1.combine(f2, IMP);
            this.lastSymbol = 'I ' + IMP + ' ' + this.openIndex() + '-' + this.idx();
            this.push(result, false, true);
            return result;
        }
    }
}

// negation introduction
// A ... B·~B => ~A
Deduction.prototype.negI = function() { // @@export
    if (this.nesting() > 0) {
        var f1 = this.get(this.openIndex());
        var f2 = this.get(this.idx());
        if (f1 && f2 && f2.isContradiction()) {
            var result = f1.negate();
            this.lastSymbol = 'I ' + NEG + ' ' + this.openIndex() + '-' + this.idx();
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
    var f = this.get(i);
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

var dd = new Deduction();
var lastBtn = null;
var okTxt = 'OK';

// perform handling before applying rule
function doApply(btn, func, num, withText, isRep) {
    lastBtn = null;
    if (withText) {
        if (btn.text() == okTxt) {
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
    var prevNesting = dd.nesting();
    // apply the rule
    try {var consq = ruleFunc.apply(dd, args);}
    catch (e) {return errmsg(e.message);}
    if (consq) {
        // add the new row(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (var i = 0; i < consq.length; i++) {
            addRow(consq[i].lit, dd.lastSymbol, false, (dd.idx() - consq.length + i + 1));
        }
        if (prevNesting > dd.nesting()) endNestingLine(dd.idx() - 1, prevNesting);
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
            if (!dd.isOnCurrentLevel(checked[i])) {
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
        dd.push(new Formula(content));
        rownum = dd.idx();
    } else {
       var rowId = 'r'+rownum;
    }
    var nesting = dd.nesting();
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
    var rownum = dd.idx();
    if ($("#r"+rownum).length == 0) return;
    $("#r"+rownum).remove();
    removeSelection();
    var nesting = dd.nesting();
    dd.pop();
    if (dd.nesting() > nesting) endNestingLine(dd.idx(), dd.nesting());
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
function showText(btn) {
    $("#extra").css("opacity","1");
    setTimeout(function(){ // trick to not miss the focus
        $("#ftxt").focus();
    }, 5);
    $("#ftxt").on("input", function() {
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
    $("#ftxt").val("");
    $("#ftxt").off("input");
    $(document).off("keypress");
    if (btn) {
        // restore button defaults
        btn.addClass("btn-default");
        btn.removeClass("btn-primary");
        btn.text(btn.data("symbol"));
    }
}
function getText() {
    return $("#ftxt").val();
}

// checkbox click handler
function oncheck() {
    hideText(lastBtn);
}

// @@skipstart
// bind rule buttons to functions and symbol buttons to insertions
$(document).ready(function() {
    $("#imp-e").click(function() {
        doApply($(this), dd.impE, 2);
    });
    $("#con-e").click(function() {
        doApply($(this), dd.conE, 1);
    });
    $("#dis-e").click(function() {
        doApply($(this), dd.disE, 3);
    });
    $("#eqv-e").click(function() {
        doApply($(this), dd.eqvE, 1);
    });
    $("#neg-e").click(function() {
        doApply($(this), dd.negE, 1);
    });
    $("#imp-i").click(function() {
        doApply($(this), dd.impI, 0);
    });
    $("#con-i").click(function() {
        doApply($(this), dd.conI, 2);
    });
    $("#dis-i").click(function() {
        doApply($(this), dd.disI, 1, true);
    });
    $("#eqv-i").click(function() {
        doApply($(this), dd.eqvI, 2);
    });
    $("#neg-i").click(function() {
        doApply($(this), dd.negI, 0);
    });
    $("#hyp").click(function() {
        doApply($(this), dd.hyp, 0, true);
    });
    $("#rep").click(function() {
        doApply($(this), dd.rep, 1, false, true);
    });
    $("#rem").click(function() {
        removeRow();
        $(this).blur();
    });
});
// @@skipend
