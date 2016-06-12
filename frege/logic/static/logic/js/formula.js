/**
 * 
 * Code for handling formulas. Contains a recursive class representation of a formula and
 * some formula functions.
 *
 * @author: Eliran Haziza
 *
 */

/* Connectives */
var NEG  = '~'
var CONJ = '*'
var DISJ = '|'
var IMPL = '>'
var EQV  = '='

/* *** ************* *** */
/* *** Formula class *** */
/* *** ************* *** */

/**
 * Constructs a new formula from a given string representation.
 */
function Formula(f) {
	this.con = null;
	this.sf1 = null;
	this.sf2 = null;
	this.literal = stripBrackets(f);
	this.analyse(this.literal);
}

/* *************** */
/* Formula methods */
/* *************** */

/**
 * Analayses a string representation of a formula and updates this formula accordingly.
 */
Formula.prototype.analyse = function(f) {
	var nesting = 0;
	var len = f.length;
	if (len === 1)
		// An atomic formula. Nothing to scan.
		return;
	for (var i = 0; i < len; i++) {
		var c = f.charAt(i);
		if (c === '(') {
			nesting++;
		} else if (c === ')') {
			nesting--;
		} else if (nesting === 0) {	
			// We are on the highest nesting level. Check for main connective.
			if (c === CONJ || c === DISJ || c === IMPL || c === EQV) {
				// Binary connective found. Create 2 sub-formulas.
				this.con = c;
				this.sf1 = new Formula(f.slice(0, i));
				this.sf2 = new Formula(f.slice(i + 1));
				return
			} else if (c === NEG) {
				// Unary connective found. Create 1 sub-formula.
				this.con = c;
				this.sf1 = new Formula(f.slice(i + 1));
				// We don't return here since a binary connective might be found
				// later and, if so, that connective would be the main one.
			}
		}
	}
}

/**
 * Assigns truth values to this formula and returns the resulting truth value.
 * Expects assignment in dictionary format.
 */
Formula.prototype.assign = function(assignment) {
	if (this.isAtomic()) {
		// An atomic formula.
		return assignment[this.literal]
	}
	switch (this.con) {
	    case NEG:
	        return !this.sf1.assign(assignment);
	    case CONJ:
	        return this.sf1.assign(assignment) && this.sf2.assign(assignment);
	    case DISJ:
	        return this.sf1.assign(assignment) || this.sf2.assign(assignment);
	    case IMPL:
	        return !this.sf1.assign(assignment) || this.sf2.assign(assignment);
	    case EQV:
	        return this.sf1.assign(assignment) == this.sf2.assign(assignment);
	}
}

/**
 * Returns a set of this formula's propositional variables.
 */
Formula.prototype.vars = function() {
	if (this.isAtomic()) {
		// Atomic formula.
		return [this.literal];
	}
	if (this.con === NEG) {
		// Unary compound formula, vars are those of sub-formula.
		return this.sf1.vars();
	}
	// Binary compound formula, uniquely merge vars of sub-formulas.
	return uniqueMerge(this.sf1.vars(), this.sf2.vars());
}

/**
 * Returns a set of all compounds descendant formulas.
 */
Formula.prototype.allCompounds = function() {
	if (this.isAtomic()) {
		return [];
	}
	if (this.con === NEG) {
		// Unary formula.
		return this.sf1.isAtomic()? [] : uniqueMerge([this.sf1], this.sf1.allCompounds());
	}
	// Binary formula. Second sub-formula is called first so as to go from right to left.
	var sub2 = this.sf2.isAtomic()? [] : uniqueMerge([this.sf2], this.sf2.allCompounds());
	var sub1 = this.sf1.isAtomic()? [] : uniqueMerge([this.sf1], this.sf1.allCompounds());
	return uniqueMerge(sub2, sub1).sort(compare);
}


/**
 * Returns a set of all compounds descendant formulas.
 */
Formula.prototype.allCompoundsTest = function() {
	// Depth-level must be less than string length, so the following should return all compounds.
	return this.getCompounds(this.literal.length);
}

/**
 * Returns a set of compounds descendant formulas down to a given depth level. Level 1 returns the direct sub-formulas, and so on.
 */
Formula.prototype.getCompounds = function(level) { // TODO: test this, also todo: reduction to above.
	if (level <= 0) return;
	if (this.isAtomic()) {
		return [];
	}
	if (this.con === NEG) {
		// Unary formula.
		return this.sf1.isAtomic()? [] : uniqueMerge([this.sf1], this.sf1.getCompounds(level - 1));
	}
	// Binary formula. Second sub-formula is called first so as to go from right to left.
	var sub2 = this.sf2.isAtomic()? [] : uniqueMerge([this.sf2], this.sf2.getCompounds(level - 1));
	var sub1 = this.sf1.isAtomic()? [] : uniqueMerge([this.sf1], this.sf1.getCompounds(level - 1));
	return uniqueMerge(sub2, sub1).sort(compare);
}

/**
 * Returns true if this formula is a descendant of the given formula.
 */
Formula.prototype.isSub = function(other) {
	if (other.isAtomic()) {
		return false;
	}
	if (other.con === NEG) {
		// Unary formula.
		return this.equals(other.sf1);
	}
	// Binary formula.
	return this.equals(other.sf1) || this.equals(other.sf2);
}

/**
 * Returns true if this formula is a descendant of the given formula.
 */
Formula.prototype.isIn = function(other) {
	if (other.isAtomic()) {
		return false;
	}
	if (other.con === NEG) {
		// Unary formula.
		return this.equals(other.sf1) || this.isIn(other.sf1);
	}
	// Binary formula.
	return this.equals(other.sf1) || this.isIn(other.sf1) || this.equals(other.sf2) || this.isIn(other.sf2);
}

/**
 * Returns true if this formula is syntactically equivalent to the given formula.
 */
Formula.prototype.equals = function(other) {
	return this.literal === other.literal;
}

/**
 * Returns a string representation of this formula.
 */
Formula.prototype.toString = function() {
	return this.literal;
}

/**
 * Returns true if this formula is a compound formula and its direct sub-formula(s)
 * are atomic.
 */
Formula.prototype.isSimpleCompound = function() {
	if (this.isAtomic()) {
		return false;
	}
	if (this.con === NEG) {
		return this.sf1.isAtomic();
	}
	return this.sf1.isAtomic() && this.sf2.isAtomic();
}

/**
 * Returns true if this formula is atomic, i.e. has no connective.
 */
Formula.prototype.isAtomic = function() {
	return !this.con;
}

Formula.prototype.str = function() {
	if (this.con === NEG) {
		return 'literal = ' + this.literal + '\ncon = ' + this.con + '\nsf1 = {' + this.sf1.literal + '}';
	}
	return 'literal = ' + this.literal + '\ncon = ' + this.con + '\nsf1 = {' + this.sf1.literal + '}\nsf2 = {' + this.sf2.literal + '}'; 
}

/* ***************** */
/* Utility functions */
/* ***************** */

/**
 * Strips the outmost brackets of a string representation of a formula.
 * Returns the resulting string.
 */
function stripBrackets(f) {
	if (f.charAt(0) === '(') {
		// Openning bracket found. Look for closure.
		var len = f.length;
		var nesting = 0;
		for (var i = 1; i < len; i++) {
			var c = f.charAt(i);
			if (c === ')') {
				if (nesting === 0) {
					// Closure found. Only strip if it's the last char.
					if (i === len - 1) return f.slice(1, len - 1);
					else return f;
				} else nesting--;
			} else if (c === '(') nesting++;
		}
	}
	return f;
}

function compare(f1, f2) {
	if (f1.isIn(f2)) {
		return 1;
	}
	if (f2.isIn(f1)) {
		return -1;
	}
	return 0;
}

function uniqueMerge(a1, a2) {
	var both = a1.concat(a2);
	var newarray = [];
	var len = both.length;
    for (var i = 0; i < len; i++) {
    	if (!contains(newarray, both[i])) {
    		newarray.push(both[i])
		}
    }
    return newarray;
}

function contains(array, obj) {
	for (var i = 0; i < array.length; i++) {
		if (typeof obj.equals === "function") {
			if (obj.equals(array[i])) {
				return true;
			}			
		} else {
			if (array[i] === obj) {
				return true;
			}			
		}
	}
	return false;
}
