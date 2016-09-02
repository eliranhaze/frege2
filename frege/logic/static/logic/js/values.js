/*
 * value assignment handling
 */

// represents a values tree
function Values(str, cols) {
    this.f = formalizeAny(str); // the formula/argument TODO: also set!
    this.cols = cols; // all column indexes
    this.idxs = []; // the selected indexes
    this.vals = {}; // the assigned values
    this.row = 0; // current row num
}

// select the i-th column
Values.prototype.select = function(i) {
    // only if i is one of the columns and wasn't already selected
    if (this.cols.indexOf(i) > -1 && this.idxs.indexOf(i) < 0) {
        this.idxs.push(i);
        this.row++;
        return i;
    }
}

// unselect the last selected
Values.prototype.unselect = function() {
    this.row--;
    return this.idxs.pop();
}

