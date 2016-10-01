/*
 * functions for handling natural deduction for propositional and predicate logic
 */

// ==========================
// deduction
// ==========================

// deduction constructor
function Deduction(obj) { // @@export
    this.formulas = [null]; // 1-indexed
    this.symbols = [''];
    this.nestingLevels = [0];
    this.nestingStack = [];
    this.reverseStack = [];
    if (obj) {
        // init values from passed object
        for (var prop in obj) {
            if (prop == 'formulas') {
                var formulas = obj[prop];
                for (var i = 0; i < formulas.length; i++) {
                    if (formulas[i]) {
                        if (isArbConst(formulas[i])) {
                            this.formulas.push(formulas[i]);
                        } else {
                            this.formulas.push(get_formula(formulas[i].lit));
                        }
                    }
                }
            } else {
                this[prop] = obj[prop];
            }
        }
    }
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
Deduction.prototype.push = function(f, symbol, nest, endnest) {
    if (this.idx() >= 80 || (f.lit && f.lit.length >= 50)) {
        throw Error('נראה לי שהגזמת...');
    }
    this.formulas.push(f);
    this.symbols.push(symbol);
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
    this.symbols.pop();
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
        this.push(result, 'E ' + IMP + ' ' + i1 + ',' + i2);
        return result;
    }
}

// conjunction elimination
// A·B => A,B
Deduction.prototype.conE = function(i, sf) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.get(i);
    if (f && f.con == CON && sf && sf.equals) {
        if (!sf.equals(f.sf1) && !sf.equals(f.sf2)) {
            throw Error('הקוניונקציה לא מכילה את הנוסחה שהוזנה')
        }
        this.push(sf, 'E ' + CON + ' ' + i);
        return sf;
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
    this.push(result, 'E ' + DIS + ' ' + i1 + ',' + i2 + ',' + i3);
    return result;
}

// equivalence elimination
// A≡B => A⊃B,B⊃A
Deduction.prototype.eqvE = function(i, sf) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.get(i);
    if (f && f.con == EQV && sf && sf.equals) {
        if (!sf.equals(f.sf1.combine(f.sf2, IMP)) && !sf.equals(f.sf2.combine(f.sf1, IMP))) {
            throw Error('לא ניתן להוציא נוסחה זו מהשקילות')
        }
        this.push(sf, 'E ' + EQV + ' ' + i);
        return sf;
    }
}

// negation elimination
// ~~A => A
Deduction.prototype.negE = function(i) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.get(i);
    if (f && f.con == NEG && f.sf1.con == NEG) {
        var result = f.sf1.sf1;
        this.push(result, 'E ' + NEG + ' ' + i);
        return result;
    }
}

// universal elimination
// ∀xPx => Pa 
Deduction.prototype.allE = function(i, c) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.get(i);
    if (f && f.quantifier == ALL) {
        var result = f.subst(c);
        this.push(result, 'E ' + ALL + ' ' + i);
        return result;
    }
}

// existential elimination
// ∃xPx, Pa ... H => H
Deduction.prototype.exsE = function(i, i1, i2) {
    if (this.nesting() > 0 && this.areOpenCloseIdx(i1, i2)) {
        var fExs = this.get(i);
        var f1 = this.get(this.openIndex());
        var f2 = this.get(this.idx());
        if (f1 && f2 && f1.contains && f2.contains) {
            var c = f1.getConstantInstanceOf(fExs);
            if (c) {
                if (f2.contains(c)) {
                    throw Error('לא ניתן להוציא את הקבוע השרירותי מתת ההוכחה');
                }
                var result = f2;
                this.push(result, 'E ' + EXS + ' ' + i + ',' + this.openIndex() + '-' + this.idx(), false, true);
                return result;
            }
        }
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
        this.push(result, 'I ' + CON + ' ' + i1 + ',' + i2);
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
        this.push(result, 'I ' + DIS + ' ' + i1);
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
        this.push(result, 'I ' + EQV + ' ' + i1 + ',' + i2);
        return result;
    }
}

// implication introduction
// A ... B => A⊃B
Deduction.prototype.impI = function(i1, i2) {
    if (this.nesting() > 0 && this.areOpenCloseIdx(i1, i2)) {
        var f1 = this.get(this.openIndex());
        var f2 = this.get(this.idx());
        if (f1 && f2 && !isArbConst(f1)) {
            var result = f1.combine(f2, IMP);
            this.push(result, 'I ' + IMP + ' ' + this.openIndex() + '-' + this.idx(), false, true);
            return result;
        }
    }
}

// negation introduction
// A ... B·~B => ~A
Deduction.prototype.negI = function(i1, i2) { // @@export
    if (this.nesting() > 0 && this.areOpenCloseIdx(i1, i2)) {
        var f1 = this.get(this.openIndex());
        var f2 = this.get(this.idx());
        if (f1 && f2 && f2.isContradiction() && !isArbConst(f1)) {
            var result = f1.negate();
            this.push(result, 'I ' + NEG + ' ' + this.openIndex() + '-' + this.idx(), false, true);
            return result;
        }
    }
}

// universal introduction
// a ... Pa => ∀xPx
Deduction.prototype.allI = function(i1, i2, v) { // @@export
    if (this.nesting() > 0 && this.areOpenCloseIdx(i1, i2)) {
        var c = this.get(this.openIndex());
        var f1 = this.get(this.idx());
        if (c && f1 && f1.contains && f1.contains(c)) {
            if (f1.contains(v)) {
                throw Error('הנוסחה כבר מכילה את המשתנה שהוזן');
            }
            var result = f1.quantify(ALL, c, v);
            this.push(result, 'I ' + ALL + ' ' + this.openIndex() + '-' + this.idx(), false, true);
            return result;
        }
    }
}

// existential introduction
// Pa => ∃xPx
Deduction.prototype.exsI = function(i, c, v) {
    if (!this.isOnCurrentLevel(i)) return;
    var f = this.get(i);
    if (f && f.contains) {
        if (!f.contains(c)) {
            throw Error('הנוסחה לא מכילה את הקבוע שהוזן');
        }
        var result = f.quantify(EXS, c, v);
        this.push(result, 'I ' + EXS + ' ' + i);
        return result;
    }
}

// hypothesis
Deduction.prototype.hyp = function(f) {
    this.push(f, 'hyp', true);
    return f;
}
 
// arbitrary constant
Deduction.prototype.arb = function(c) {
    // check if const already appeared
    for (var i = 0; i < this.formulas.length; i++) {
        var f = this.formulas[i];
        if (f && ((isArbConst(f) && f == c) || (f.contains && f.contains(c)))) {
            throw Error('קבוע זה כבר הופיע בהוכחה');
        }
    }
    this.push(c, 'arb const', true);
    return c;
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
    this.push(f, 'rep ' + i);
    return f;
}

Deduction.prototype.areOpenCloseIdx = function(i1, i2) {
    if (i2 == undefined) i2 = i1;
    return (i1 == this.openIndex() && i2 == this.idx()) || (i1 == this.openIndex() && i2 == this.idx());
}

function isArbConst(x) {
    return typeof x == 'string' && x.length == 1 && isLower(x);
}

// ==========================
// user interaction
// ==========================

var dd = new Deduction();

// perform handling before applying rule
function doApply(btn, func, num, txtKW, allowOffLevel) {
    if (func == dd.impI || func == dd.negI || func == dd.allI || func == dd.exsE) {
        // subproof rule
        num += dd.idx() == dd.openIndex()? 1 : 2;
    }
    if (txtKW) {
        if (validateSelection(num)) {
            showText(btn, func, num, txtKW);
        }
    } else {
        hideText();
        applyRule(func, num, false, allowOffLevel);
    }
    btn.blur();
}

// general function for applying a rule, gets rule-specific parameters and callbacks
function applyRule(ruleFunc, numRows, inputHandler, allowOffLevel) {
    if (!validateSelection(numRows, allowOffLevel)) {
        return;
    }
    var args = getChecked();
    if (inputHandler) {
        var input = getText();
        if (!input) return errmsg("יש להזין ערך");
        try {
            inputHandler(input, args);
        } catch (e) {
            return errmsg(e.message);
        }
    }
    // apply the rule
    try {var consq = ruleFunc.apply(dd, args);}
    catch (e) {return errmsg(e.message);}
    if (consq) {
        // add the new row(s) to the deduction
        if (!(consq instanceof Array)) { consq = [consq];}
        for (var i = 0; i < consq.length; i++) {
            var formula = consq[i];
            if (!isArbConst(consq[i])) var formula = formula.lit;
            isArb = ruleFunc == Deduction.prototype.arb;
            addRow(formula, dd.symbols[dd.symbols.length-1], (dd.idx() - consq.length + i + 1), isArb);
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


// ======================================================
// rules input handlers
// ======================================================

function formulaInputHandler(input, ruleArgs) {
    var formula = get_formula(input);
    ruleArgs.push(formula);
}

function arbInputHandler(input, ruleArgs) {
    if (!isArbConst(input)) throw Error('קלט לא תקין');
    ruleArgs.push(input);
}

function arbsInputHandler(input, ruleArgs) {
    var inputs = input.split(',');
    if (inputs.length != 2) throw Error('קלט לא תקין');
    for (var i = 0; i < inputs.length; i++) {
        arbInputHandler($.trim(inputs[i]), ruleArgs);
    }
}

// ======================================================

function removeSelection() {
    $("input[type=checkbox]").prop("checked", false);
}

// return true if user selection is ok, otherwise print error and return false
function validateSelection(numRows, allowOffLevel) {
    if (numRows > 0) {
        var checked = getChecked();
        if (checked.length != numRows) {
            var words = ["", "שורה אחת", "שתי שורות", "שלוש שורות"];
            errmsg("יש לבחור "+words[numRows]+" על מנת להשתמש בכלל זה");
            return false;
        }
        if (allowOffLevel) return true;
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
// this changes display only, and not the deduction object; all changes to it have to be done prior
function addRow(content, symbol, rownum, isArb) {
    var rowId = 'r'+rownum;
    var nesting = dd.nestingLevels[rownum];
    // handle nesting
    if (isArb) {
        content = '<div class="dd-arb">'+content+'</div>';
    }
    for (var i = 0; i < nesting; i++) content = addNesting(content, rownum, nesting - i);
    // add the row
    $('#deduction tr:last').after(
        '<tr id="'+rowId+'">'+
          '<td class="dd-num""><input type="checkbox" id="cb'+rownum+'" name="'+rownum+'" onclick="oncheck()">'+rownum+'. </input></td>'+
          '<td id="f'+rownum+'">'+content+'</td>'+
          '<td class="dd-just">'+symbol+'</td>'+
        '</tr>'
    );
    // handle end of nesting cases
    if (rownum > 1) {
        var prevNesting = dd.nestingLevels[rownum-1];
        if (prevNesting > nesting) endNestingLine(rownum-1, prevNesting);
    }
}

// remove selected deduction rows (must be last rows)
function removeRows() {
    var checkedRows = getChecked();
    if (!checkedRows || checkedRows.length == 0) {
        removeRow();
        return;
    }
    // check that all are last rows
    var len = checkedRows.length;
    for (var i = 0; i < checkedRows.length; i++) {
        if (checkedRows.indexOf(dd.idx()-i) < 0) {
            errmsg('ניתן למחוק שורות רק מהסוף');
            return;
        }
    }
    // remove the last rows
    for (var i = 0; i < checkedRows.length; i++) {
        removeRow();
    }
}

// remove the last deduction row 
function removeRow() {
    // delete by row id (premises don't have row id and so cannot be deleted)
    var rownum = dd.idx();
    if (dd.symbols[rownum] == 'prem') return; // premises cannot be removed
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

// add an end of nesting indication
function endNestingLine(index, nesting) {
    $("#nst"+index+""+nesting).toggleClass("dd-hyp-end");
}

// utils
function getChecked() {
    return $('input:checkbox:checked').map(function() {
        return parseInt(this.name);
    }).get();
}
function showText(btn, func, num, txtKW) {
    $("#extra").show();
    if (txtKW.hideBtns) {
        $("#extbtns").hide();
    } else {
        $("#extbtns").show();
    }
    $("#ftxtLbl").html(txtKW.label);
    $("#ftxtHint").html(txtKW.hint);
    setTimeout(function(){ // trick to not miss the focus
        $("#ftxt").focus();
    }, 5);
    $("#txtOk").data('btnData', {
        func: func,
        num: num,
        handler: txtKW.handler, 
    });
}
function hideText() {
    $("#extra").hide();
    $("#ftxt").val("");
    $("#ftxt").off("input");
    $("#txtOk").data('btnData', null);
}
function textOk() {
    btnData = $("#txtOk").data('btnData');
    if (btnData) {
        if (applyRule(btnData.func, btnData.num, btnData.handler)) {
            hideText();
        }
    }
}
function getText() {
    return $("#ftxt").val();
}

// checkbox click handler
function oncheck() {
    hideText();
}

// @@skipstart
// bind rule buttons to functions and symbol buttons to insertions
$(document).ready(function() {
    $("#imp-e").click(function() {
        doApply($(this), dd.impE, 2);
    });
    $("#con-e").click(function() {
        doApply($(this), dd.conE, 1, {
            label: 'נוסחה',
            hint: 'יש להזין נוסחה עבור הוצאת קוניונקציה',
            handler: formulaInputHandler
        });
    });
    $("#dis-e").click(function() {
        doApply($(this), dd.disE, 3);
    });
    $("#eqv-e").click(function() {
        doApply($(this), dd.eqvE, 1, {
            label: 'נוסחה',
            hint: 'יש להזין נוסחה עבור הוצאת שקילות',
            handler: formulaInputHandler
        });
    });
    $("#neg-e").click(function() {
        doApply($(this), dd.negE, 1);
    });
    $("#all-e").click(function() {
        doApply($(this), dd.allE, 1, {
            label: 'קבוע',
            hint: 'יש להזין קבוע עבור הוצאת כמת כולל',
            handler: arbInputHandler,
            hideBtns: true,
        });
    });
    $("#exs-e").click(function() {
        doApply($(this), dd.exsE, 1, null, true);
    });
    $("#imp-i").click(function() {
        doApply($(this), dd.impI, 0);
    });
    $("#con-i").click(function() {
        doApply($(this), dd.conI, 2);
    });
    $("#dis-i").click(function() {
        doApply($(this), dd.disI, 1, {
            label: 'נוסחה',
            hint: 'יש להזין נוסחה עבור הכנסת דיסיונקציה',
            handler: formulaInputHandler
        });
    });
    $("#eqv-i").click(function() {
        doApply($(this), dd.eqvI, 2);
    });
    $("#neg-i").click(function() {
        doApply($(this), dd.negI, 0);
    });
    $("#all-i").click(function() {
        doApply($(this), dd.allI, 0, {
            label: 'משתנה',
            hint: 'יש להזין משתנה עבור הכנסת כמת כולל',
            handler: arbInputHandler,
            hideBtns: true,
        });
    });
    $("#exs-i").click(function() {
        doApply($(this), dd.exsI, 1, {
            label: 'קבוע ומשתנה',
            hint: 'יש להזין קבוע ומשתנה מופרדים בפסיק עבור הכנסת כמת ישי',
            handler: arbsInputHandler,
            hideBtns: true,
        });
    });
    $("#hyp").click(function() {
        doApply($(this), dd.hyp, 0, {
            label: 'היפותזה',
            hint: 'יש להזין נוסחה שתשמש כהיפותזה',
            handler: formulaInputHandler
        });
    });
    $("#arb").click(function() {
        doApply($(this), dd.arb, 0, {
            label: 'קבוע',
            hint: 'יש להזין קבוע שרירותי',
            handler: arbInputHandler,
            hideBtns: true,
        });
    });
    $("#rep").click(function() {
        doApply($(this), dd.rep, 1, null, true);
    });
    $("#rem").click(function() {
        removeRows();
        $(this).blur();
    });
    $("#txtOk").click(function() {
        textOk();
    });
    $("#txtCnl").click(function() {
        hideText();
    });
    $(document).keypress(function(e) {
        if (e.which == 13) { // Enter 
            $("#txtOk").click();
        }
    });
});
// @@skipend
