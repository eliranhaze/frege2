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
                if (!(isAlpha(next) || next == NEG || next == '(')) {
                    throw new Error(generr);
                }
            }
        } else if (nesting == 0) {
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
    return c == CON || c == DIS || c == IMP || c == EQV;
}

function isCommutative(c) {
    return c == CON || c == DIS || c == EQV;
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
