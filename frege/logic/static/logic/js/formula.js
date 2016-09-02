/*
 * representation of propositional and first order formulas
 */

// ==========================
// constants
// ==========================

var NEG = '~'; // @@export
var CON = '·'; // @@export
var DIS = '∨'; // @@export
var IMP = '⊃'; // @@export
var EQV = '≡'; // @@export
var ALL = '∀'; // @@export
var EXS = '∃'; // @@export
var THF = '∴'; // @@export

// ==========================
// formula 
// ==========================

// formula constructor
function Formula(f) { // @@export
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
                if (!(isAlpha(next) || next == NEG || next == '(' || isQuantifier(next))) {
                    throw new Error(generr);
                }
            }
        } else if (nesting == 0) {
            // highest nesting level, check for main connective
            if (isBinary(c)) {
                var _sf1 = f.slice(0, i);
                var _sf2 = f.slice(i+1);
                this.con = c;
                this.sf1 = new this.constructor(_sf1); 
                this.sf2 = new this.constructor(_sf2); 
                if (!this.sf1.validateSub(_sf1) || !this.sf2.validateSub(_sf2)) {
                    throw new Error(generr);
                }
                return;
            } else if (c == NEG) {
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
        this.sf1 = new this.constructor(sf);
        return;
    }
    throw new Error(generr);
}

Formula.prototype.isAtomic = function() {
    return this.lit.length == 1 && isAlpha(this.lit);
}

// check if a formula is a contradiction of the form A·~A
Formula.prototype.isContradiction = function() {
    if (this.con == CON) {
        return this.sf1.isNegationOf(this.sf2) || this.sf2.isNegationOf(this.sf1);
    }
    return false;
}

Formula.prototype.isNegationOf = function(other) {
    return this.con == NEG && this.sf1.equals(other);
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
        f = get_formula(this.lit); // this is a bit of a hack    
        f.con = c;
        f.sf1 = this;
        f.sf2 = other;
        f.lit = this.wrap() + c + other.wrap();
        return f;
    }
}

// return a negation of this formula
Formula.prototype.negate = function() {
    f = get_formula(this.lit);    
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
// predicate formula 
// ==========================

// predicate formula constructor
function PredicateFormula(f) { // @@export
    this.quantifier = null;
    this.quantified = null;
    Formula.call(this, f);
}

PredicateFormula.prototype = Object.create(Formula.prototype);
PredicateFormula.prototype.constructor = PredicateFormula;

PredicateFormula.prototype.analyze = function(f) {
    if (isQuantifier(this.lit.charAt(0)) && quantifierRange(this.lit) == this.lit.slice(2)) {
        if (this.lit.length < 4) throw new Error('טווח כמת קטן מדי');
        this.quantifier = this.lit.charAt(0);
        this.quantified = this.lit.charAt(1);
        if (!isLower(this.quantified)) throw new Error('משתנה כמת לא תקין');
        this.sf1 = new PredicateFormula(this.lit.slice(2));
    } else {
        Formula.prototype.analyze.call(this, f);
    }
}

// substitute a constant for the first quantified variable of this formula, returns a formula
PredicateFormula.prototype.subst = function(c) {
    if (this.quantifier) {
        return new PredicateFormula(this.sf1.substFree(c, this.quantified));
    }
}

// substitute a constant for an given unbound variable, returns a string
PredicateFormula.prototype.substFree = function(c, v) {
    if (this.quantifier) {
        if (this.quantified == v) {
            return this.lit;
        } else {
            return this.quantifier + this.quantified + new PredicateFormula(this.sf1.substFree(c, v)).wrap();
        }
    } else if (isBinary(this.con)) {
        return new PredicateFormula(this.sf1.substFree(c, v))
                   .combine(new PredicateFormula(this.sf2.substFree(c, v)), this.con).lit;
    } else if (this.con == NEG) {
        return new PredicateFormula(this.sf1.substFree(c, v)).negate().lit;
    } else if (this.isAtomic()) {
        return this.lit.replace(new RegExp(v, 'g'), c);
    }
}

// if this instantiantes the given quantified formula, returns the constant that
// substitutes the quantified variable
// e.g.: Pa.getConstantInstanceOf(∃xPx) = a
PredicateFormula.prototype.getConstantInstanceOf = function(f) {
    if (f.quantifier) {
        for (var i = 0; i < this.lit.length; i++) {
            var c = this.lit.charAt(i);
            if (isLower(c) && f.subst(c).equals(this)) {
                return c;
            }
        }
    }
}

// quantify over a variable in place of a given constant
var _variables = ['x', 'y', 'z', 'w', 'u' ,'v', 't', 's', 'r'];
PredicateFormula.prototype.quantify = function(quantifier, c) {
    if (this.contains(c)) {
        for (var i = 0; i < _variables.length; i++) {
            if (!this.contains(_variables[i])) {
                var v = _variables[i];
                break;
            }
        }
        if (v) {
            var openFormula = new PredicateFormula(
                this.lit.replace(new RegExp(c, 'g'), v)
            );
            return new PredicateFormula(
                quantifier + v + openFormula.wrap()
            );
        }
    }
}

PredicateFormula.prototype.isAtomic = function() {
    return isPredicateAtomic(this.lit);
}

PredicateFormula.prototype.contains = function(c) {
    return this.lit.indexOf(c) > -1;
}

// ==========================
// formula utils
// ==========================

function isAlpha(a) {
    return a.toLowerCase() != a.toUpperCase();
}

function isLower(a) {
    return isAlpha(a) && a == a.toLowerCase();
}

function isUpper(a) {
    return isAlpha(a) && a == a.toUpperCase();
}

function isBinary(c) {
    return c == CON || c == DIS || c == IMP || c == EQV;
}

function isCommutative(c) {
    return c == CON || c == DIS || c == EQV;
}

function isQuantifier(q) {
    return q == ALL || q == EXS;
}

// get the quantifier range of a quantified formula string
function quantifierRange(f) { // @@export
    if (f.length > 3 && isQuantifier(f.charAt(0))) {
        var start = f.charAt(2);
        var remaining = f.slice(2);
        if (start == '(') {
            var qrange = '';
            var stack = [];
            for (var i = 0; i < remaining.length; i++) {
                var c = remaining.charAt(i);
                qrange += c;
                if (c == '(') stack.push(c);
                else if (c == ')') stack.pop();
            if (stack.length == 0) return qrange;
            } 
        } else if (start == NEG) {
            return start + quantifierRange(f.replace('~',''));
        } else if (isQuantifier(start)) {
            var remainingRange = quantifierRange(remaining);
            if (!remainingRange) throw new Error('כימות לא תקין');
            return remaining.slice(0,2) + remainingRange;
        } else {
            var qrange = '';
            for (var i = 0; i < f.length - 3; i++) {
                var cur = remaining.slice(0,i+2);
                if (isPredicateAtomic(cur)) {
                    qrange = cur;
                } else break;
            }
            return qrange;
        }
    }
}

function isPredicateAtomic(s) {
    if (s.length > 1 && isUpper(s.charAt(0))) {
        for (var i = 1; i < s.length; i++) {
            if (!isLower(s.charAt(i))) return false;
        }
        return true;
    }
    return false;
}

// strip brackets and remove spaces from a formula string
function form(f) {
    return stripBrackets(f).replace(/ /g,'');
}

// strip outmost brackets from a formula
function stripBrackets(f) {
    if (f.charAt(0) == '(' && f.charAt(f.length-1) == ')') {
        // brackets detected, make sure they can be stripped 
        var nesting = 0;
        for (var i = 0; i < f.length; i++) {
            var c = f.charAt(i);
            if (c == ')') {
                nesting--;
                if (nesting == 0) {
                    // closure found for the opening bracket, only strip if it's last
                    if (i == f.length - 1) { 
                        // strip recursively
                        return stripBrackets(f.slice(1, f.length - 1));
                    }
                    return f;
                }
            } else if (c == '(') {
                nesting++;
            }
        }   
    }
    return f;
}

// ==========================
// argument 
// ==========================

// argument constructor
function Argument(str, cls) { // @@export
    try {
        if (!cls) cls = Formula;
        var splits = str.split(THF);
        this.conclusion = new cls(splits[1]);
        this.premises = [];
        var prmSplits = splits[0].split(',');
        if (prmSplits.length > 1 || prmSplits[0] != '') {
            for (var i = 0; i < prmSplits.length; i++) {
                this.premises.push(new cls(prmSplits[i]));
            }
        }
    }
    catch (e) {
        throw new Error('טיעון לא תקין');
    } 
}

function get_formula(str) {
    try {
        return new Formula(str);
    } catch (e) {
        return new PredicateFormula(str);
    }
}

function get_argument(str) {
    try {
        return new Argument(str);
    } catch (e) {
        return new Argument(str, PredicateFormula);
    }
}

function get_set(str) {
    var set = [];
    var splits = str.split(',');
    for (var i = 0; i < splits.length; i++) {
        set.push(get_formula(splits[i]));
    }
    return set;
}

function has_argument_form(str) {
    return str.indexOf(THF) > -1;
}

function has_predicate_form(obj) {
    if (obj instanceof Argument) {
        return has_predicate_form(obj.conclusion);
    }
    return obj instanceof PredicateFormula;
}

function is_formula_type(typeName) {
    return typeName.indexOf('Formula') > -1;
}

function is_argument_type(typeName) {
    return typeName.indexOf('Argument') > -1;
}

function is_predicate_type(typeName) {
    return typeName.indexOf('Predicate') > -1;
}

function formalize(str, expectedType) {

    if (is_formula_type(expectedType)) {
        if (has_argument_form(str)) {
            throw new Error('ההצרנה צריכה להיות טענה');
        }
        var obj = get_formula(str);
    } else { // argument type
        if (!has_argument_form(str)) {
            throw new Error('ההצרנה צריכה להיות טיעון');
        }
       var obj = get_argument(str);
    }

    if (is_predicate_type(expectedType)) {
        if (!has_predicate_form(obj)) {
            throw new Error('ההצרנה צריכה להיות בתחשיב הפרדיקטים');
        }
    } else {
        if (has_predicate_form(obj)) {
            throw new Error('ההצרנה צריכה להיות בתחשיב הפסוקים');
        }
    }

    return obj;
}

function formalizeAny(str) {
    var funcs = [get_formula, get_argument, get_set];
    for (var i = 0; i < funcs.length; i++) {
        try {
            return funcs[i](str);
        } catch (e) {}
    }
}
