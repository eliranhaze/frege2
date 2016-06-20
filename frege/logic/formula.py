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
                        self.sf1 = Formula(self.literal[:i])
                        self.sf2 = Formula(self.literal[i+1:])
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
        if self.is_atomic():
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

    def variables(self):
        pass

    def is_atomic(self):
        return not self.con