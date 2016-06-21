# -*- coding: utf-8 -*-
"""
Code for handling classical propositional logic formulas.
"""

# Connectives
NEG = '~'
CON = '*'
DIS = '|'
IMP = '>'
EQV = '='

BINARY_CONNECTIVES = set([CON, DIS, IMP, EQV])

class Option(object):

    def __init__(self, num, desc):
        self.num = num
        self.desc = desc

    @classmethod
    def for_formula(cls):
        return [cls.Tautology, cls.Contingency, cls.Contradiction]

    @classmethod
    def for_argument(cls):
        return [cls.Valid, cls.Invalid]

    @classmethod
    def for_set(cls):
        return [cls.Consistent, cls.Inconsistent]

    def __unicode__(self):
        return self.desc

    __repr__ = __unicode__
    __str__ = __unicode__

# set options
Tautology = Option(1, 'טאוטולוגיה')
Contingency = Option(2, 'קונטינגנציה')
Contradiction = Option(3, 'סתירה')
Valid = Option(4, 'תקף')
Invalid = Option(5, 'בטל')
Consistent = Option(6, 'עקבית')
Inconsistent = Option(7, 'לא עקבית')

FORMULA_OPTIONS = [Tautology, Contingency, Contradiction]
ARGUMENT_OPTIONS = [Valid, Invalid]
SET_OPTIONS = [Consistent, Inconsistent]

class Formula(object):

    def __init__(self, string):
        string = string.strip()
        self._analyze(string)
        self._validate()

    def _analyze(self, string):
        if not string:
            raise ValueError('formula cannot be empty')

        self.con = None
        self.sf1 = None
        self.sf2 = None
        self.literal = self._strip(string)

        nesting = 0
        if (len(self.literal) == 1):
            # atomic formula
            return
        for i, c in enumerate(self.literal):
            if c == '(':
                nesting += 1
                # validate next char
                nxt = self.literal[i+1]
                if not (nxt.isalpha() or nxt == NEG or nxt == '('):
                    raise ValueError("illegal character %s after %s" % (nxt, c))
            elif c == ')':
                nesting -= 1
            elif nesting == 0:
                try:
                    # highest nesting level, check for main connective
                    if c in BINARY_CONNECTIVES:
                        # binary connective, create 2 sub formulas and return
                        self.con = c
                        literals = self.literal[:i], self.literal[i+1:]
                        self.sf1 = Formula(literals[0])
                        self.sf2 = Formula(literals[1])
                        # check that sub formulas are properly formed
                        for i, sf in enumerate([self.sf1, self.sf2]):
                            literal = literals[i]
                            if sf.is_binary and not (literal[0] == '(' and literal[-1] == ')'):
                                raise ValueError('missing parentheses in sub formula') 
                        return
                    if c == NEG:
                        # unary connective, create 1 sub formula
                        if self.con:
                            # concatenated negations, sub formula was already created
                            assert self.sf1
                        else:
                            self.con = c
                            self.sf1 = Formula(self.literal[i+1:])
                            # do not return here since a binary connective might be found
                            # later and, if so, that would be the main connective
                except ValueError:
	            raise ValueError('%s is not a syntactically valid formula' % string)
            elif nesting < 0:
                raise ValueError('unbalanced parentheses in %s' % string)

    def _strip(self, string):
        """ strip all outmost brackets of a string representation of a formula """
        if not string:
            return string
        if string[0] == '(' and string[-1] == ')':
            # brackets detected on both end side, but we must make sure they actually are the outer
            # most ones, and not a case like '(p&q)&(r&s)', which should not be stripped
            nesting = 0
            for i, c in enumerate(string):
                if c == ')':
                    nesting -= 1
                    if nesting == 0:
                        # closure found for the opening bracket, only strip if it's last
                        if i == (len(string) - 1):
                            # strip recursively
                            return self._strip(string[1:-1])
                        return string
                elif c == '(':
                    nesting += 1
        return string 

    def _validate(self):
        if self.is_atomic:
            assert not self.sf1 and not self.sf2
            if len(self.literal) > 1:
                raise ValueError('%s is invalid; only 1 letter atoms are allowed' % self.literal)
            if len(self.literal) == 0:
                raise ValueError('empty formula')
            if not self.literal.isalpha():
                raise ValueError('%s must be a letter')
        else:
            assert len(self.literal) > 1
            # validate of sub formulas is not called here since it is called while creating them above
            assert self.sf1
            if self.con in BINARY_CONNECTIVES:
                assert self.sf2

    @property
    def variables(self):
        """ return a list of variables, merged and sorted """
        if not hasattr(self, '_vars'):
            var_list = self._var_list()
            var_list = list(set(var_list))
            var_list.sort()
            self._vars = var_list
        return self._vars

    def _var_list(self):
        """ return a list of variables, not merged """
        if self.is_atomic:
            return [self.literal]
        if self.is_unary:
            return self.sf1._var_list()
        # binary
        return self.sf1._var_list() + self.sf2._var_list() 

    def assign(self, assignment):
        if len(self.variables) > len(assignment):
            raise ValueError('incorrect assignment size, should be %d' % len(self.variables))
        if any (v not in assignment for v in self.variables):
            raise ValueError('missing variables in assignment %s' % assignment)
        if self.is_atomic:
            return assignment[self.literal]
        if self.con == NEG: 
            return not self.sf1.assign(assignment)
        elif self.con == CON:
            return self.sf1.assign(assignment) and self.sf2.assign(assignment)
        elif self.con == DIS:
           return  self.sf1.assign(assignment) or self.sf2.assign(assignment)
        elif self.con == IMP:
           return  not self.sf1.assign(assignment) or self.sf2.assign(assignment)
        elif self.con == EQV:
           return  self.sf1.assign(assignment) == self.sf2.assign(assignment)

    def options(self):
        return FORMULA_OPTIONS

    @property
    def correct_option(self):
        tt = TruthTable(self)
        options = set([Tautology, Contradiction])
        for var_values in tt.values:
            satisfied = self.assign({
                var : value for var, value in zip(tt.variables, var_values)
            })
            if not satisfied and Tautology in options:
                options.remove(Tautology)
            elif satisfied and Contradiction in options:
                options.remove(Contradiction)
            if not options:
                return Contingency
        assert len(options) == 1
        return options.pop()

    @property
    def is_atomic(self):
        return not self.con
    @property
    def is_unary(self):
        return self.con == NEG
    @property
    def is_binary(self):
        return self.con in BINARY_CONNECTIVES

    def __unicode__(self):
        return self.literal

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, unicode(self))

    __str__ = __unicode__

class TruthTable(object):

    def __init__(self, formula):
        self.formula = formula
        self.variables = formula.variables
        self.values = self._values(self.variables)

    def size(self):
        return len(self.values)

    def _values(self, variables):
        values = []
        num_rows = 2**len(variables)
        num_cols = len(variables)
        for i in range(num_rows):
            row = []
            for j in range(num_cols):
                streak = 2**j
                relative = i % (streak * 2)
                row.insert(0, relative < streak)
            values.append(row)
        return values

