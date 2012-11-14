
from collections import namedtuple

__all__ = [
    'Pos',
    'Token',
    'SExp',
    'VarExp',
    'NumExp',
    'BoolExp',
    'StrExp',
    'LamExp',
    'AppExp',
    'IfExp',
    'LetRecExp'
    ]

################################################################################
## Parser types
################################################################################

# A position object for tracking location in the source file
Pos = namedtuple('Pos', ['line', 'col'])
# A token object for holding literals and their position in the source file
Token = namedtuple('Token', ['pos', 'val'])

class SExp(list):
    """A S-expression.

    @type pos: Pos
    @param pos: position of the S-expression in the source file
    @type: A list of SExps and/or Tokens
    @param args: SExps or Tokens contained within this S-expression
    """
    def __init__(self, pos, *args):
        self.pos = pos
        super(SExp, self).__init__(*args)
    def __repr__(self):
        return 'SExp(' + ', '.join(repr(e) for e in self) + ')'


################################################################################
## Scheme Expressions
################################################################################

# VarExp = namedtuple('VarExp', 'name')
# LamExp = namedtuple('LamExp', 'vars, bodyExp')
# AppExp = namedtuple('AppExp', 'funcExp, argExps')
# IfExp  = namedtuple('IfExp',  'condExp, thenExp, elseExp')

## Atomic Expressions
class AtomicExp: pass

class VarExp(AtomicExp):
    """A variable.

    @type name: String
    @param name: The name of the variable
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.name)

class NumExp(AtomicExp):
    """A number.

    @type val: Number
    @param val: The value
    """
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return str(self.val)

class BoolExp(AtomicExp):
    """A boolean.

    @type val: Bool
    @param val: The value
    """
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "#t" if self.val else "#f"

class StrExp(AtomicExp):
    """A string.

    @type val: String
    @param val: The value
    """
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return '"{0}"'.format(self.val)

class LamExp(AtomicExp):
    """A lambda expression.

    @type vars: A List of VarExps
    @param vars: The formal parameters of the lambda
    @type bodyExp: Any Scheme expression
    @param bodyExp: The body of the lambda
    """
    def __init__(self, vars, bodyExp):
        if isinstance(vars, AppExp):
            vars = vars.tolist()
        self.vars = vars
        self.bodyExp = bodyExp

    def __repr__(self):
        return '(lambda ({0}) {1})'.format(' '.join(map(str, self.vars)),
                                           self.bodyExp)

## More complex expressions
class AppExp:
    """A lambda application.

    @type funcExp: Any Scheme expression
    @param funcExp: The function being applied
    @type argExps: A List of Scheme Expressions (not passed as a list though!)
    @param argExps: The arguments to the function
    """
    def __init__(self, funcExp, *argExps):
        self.funcExp = funcExp
        self.argExps = argExps

    def __repr__(self):
        return '({0} {1})'.format(self.funcExp,
                                  ' '.join(map(repr, self.argExps)))

    def tolist(self):
        lst = [self.funcExp]
        lst.extend(self.argExps)
        return lst

class IfExp:
    """An if expression.

    All three parameters can be any Scheme expression.
    """
    def __init__(self, condExp, thenExp, elseExp):
        self.condExp = condExp
        self.thenExp = thenExp
        self.elseExp = elseExp

    def __repr__(self):
        return '(if {0} {1} {2})'.format(self.condExp, self.thenExp,
                                         self.elseExp)

class LetRecExp:
    """A letrec expression.

    @type varExp: A VarExp
    @param varExp: The symbol to which the function will be bound
    @type funcExp: A LamExp
    @param funcExp: The recursive function
    @type bodyExp: Any Scheme expression
    @param bodyExp: The body of the LetRec expression
    """
    def __init__(self, varFuncExps, bodyExp):
        if isinstance(varFuncExps, AppExp):
            varFuncExps = varFuncExps.tolist()
        for i, expr in enumerate(varFuncExps):
            if isinstance(expr, AppExp):
                varFuncExps[i] = expr.tolist()
        self.varFuncExps = varFuncExps
        self.bodyExp = bodyExp

    def __repr__(self):
        return '(letrec ({0}) {1})'.format(' '.join('({0} {1})'.format(v, f) for v, f in self.varFuncExps),
                                                 self.bodyExp)
