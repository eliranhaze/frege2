/**
 * 
 * Code for handling truth tables.
 *
 * @author: Eliran Haziza
 *
 */

/* *** ***************** *** */
/* *** Truth table class *** */
/* *** ***************** *** */

/**
 * Constructs a new truth table from a given formula object.
 */
function TruthTable(formula) {
	this.formulas = [formula].concat(formula.allCompounds())
	this.vars = formula.vars().sort().reverse();
	this.values = values(this.vars);
	this.initTruthSelections();
	this.initHighlights();
}

/* ******************* */
/* Truth table methods */
/* ******************* */

/**
 * Initializes truth value selections.
 */
TruthTable.prototype.initTruthSelections = function() {
	var rows = this.values.length;
	var cols = this.formulas.length;
	// Initialize with nulls to inidicate no selection.
	this.selections = new2darray(rows, cols, null);
	this.wrongs = newarray(cols, false);
};

/**
 * Initializes column highlights.
 */
TruthTable.prototype.initHighlights = function() {
	this.varhl = newarray(this.vars.length, false);
	this.forhl = newarray(this.formulas.length, false);
};

/**
 * Assigns the truth values in the given row to the formula in the given column.
 */
TruthTable.prototype.assign = function(row, col) {
	var assignment = {};
	// Create a truth assignment according to the truth values in the given row.
	for (var i = 0; i < this.vars.length; i++) {
		assignment[this.vars[i]] = this.values[row][i];
	}
	// Assign to the formula.
	return this.formulas[col].assign(assignment);
}

/**
 * Selects a turth value in the given row and column. Deselects if already selected.
 */
TruthTable.prototype.select = function(row, col, value) {
	var selectRow = this.selections[row];
	if (selectRow[col] === null) selectRow[col] = value;
	else selectRow[col] = null;
}

/**
 * Clears all truth value selections.
 */
TruthTable.prototype.clearSelections = function() {
	for (var row = 0; row < this.values.length; row++) {
		for (var col = 0; col < this.formulas.length; col++) {
			this.selections[row][col] = null;
			this.wrongs[col] = false;
		}
	}
}

/**
 * Returns true if all table cells have a truth selection.
 */
TruthTable.prototype.isFullySelected = function() {
	for (var row = 0; row < this.values.length; row++) {
		for (var col = 0; col < this.formulas.length; col++) {
			if (this.selections[row][col] === null) 
				return false;
		}
	}
	return true;
}

/**
 * Returns true if all selections are correct, false if some are incorrect.
 * If any selection is empty this returns null.
 */
TruthTable.prototype.isCorrect = function() {
// TODO: this could be made simpler by checking fully selected first. Consider this.
// Or maybe just assume fullySelected was already checked. for simplicity.
	var correct = true; // Until proven otherwise.
	initarray(this.wrongs, false);
	for (var row = 0; row < this.values.length; row++) {
		for (var col = 0; col < this.formulas.length; col++) {
			var selection = this.selections[row][col]; 
			if (selection === null)	return null;
			else {
				if (this.assign(row, col) !== selection) {
					this.wrongs[col] = true;
					correct = false;
					// Keep checking and do not return here, since the table
					// might not be fully selected, and then null is returned.
				}
			}
		}
	}
	return correct;
}

/**
 * Highlights direct sub-formulas of given formula.
 */
TruthTable.prototype.highlight = function(formula) {
	for (var i = 0; i < this.vars.length; i++) {
		this.varhl[i] = new Formula(this.vars[i]).isSub(formula); // TODO: consider turning vars into formulas. And then we don't have to instatiate a Formula object here.
	}
	for (var i = 0; i < this.formulas.length; i++) {
		this.forhl[i] = this.formulas[i].isSub(formula);
	}
}

/**
 * Clears all highlights.
 */
TruthTable.prototype.clearHighlights = function(formula) {
	for (var i = 0; i < this.vars.length; i++) {
		this.varhl[i] = false;
	}
	for (var i = 0; i < this.formulas.length; i++) {
		this.forhl[i] = false;
	}
}

/* ***************** */
/* Utility functions */
/* ***************** */

/**
 * Returns a matrix of truth values according to the number of given propositional variables.
 */
function values(vars) {
	var rowcount = Math.pow(2, vars.length);
	var colcount = vars.length;
	var vals = new Array(rowcount);
	for (i = 0; i < rowcount; i++) {
		vals[i] = new Array(colcount);
		for (j = 0; j < colcount; j++) {
			var streak = Math.pow(2, j);
			var relative = i % (streak * 2);
			vals[i][j] = relative < streak;
		}
	}
	return vals;
}
