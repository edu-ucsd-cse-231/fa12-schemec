
from collections import namedtuple

__all__ = [
    'Pos',
    'Token',
    'SExp',
    'AtomicExp',
    'VarExp',
    'NumExp',
    'BoolExp',
    'true',
    'false',
    'VoidExp',
    'void',
    'StrExp',
    'LamExp',
    'AppExp',
    'IfExp',
    'LetRecExp',
    'BeginExp',
    'SetExp',
    'SetThenExp',
    'gensym'
    ]

class GenSym:
    n = 1
    @classmethod
    def __call__(cls, sym=''):
        sym += str(cls.n)
        cls.n += 1
        return VarExp(sym)
gensym = GenSym()

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
        super(SExp, self).__init__(args)
    def __getitem__(self, key):
        if isinstance(key, slice):
            return SExp(self.pos, *super(SExp, self).__getitem__(key))
        else:
            return super(SExp, self).__getitem__(key)
    def __repr__(self):
        return 'SExp(' + ', '.join(repr(e) for e in self) + ')'

# import here to avoid circular import dependency
from schemec.sexp import pretty
unkpos = Pos(-1, -1)

################################################################################
## Scheme Expressions
################################################################################

## Atomic Expressions
class AtomicExp:
    def map(self, f):
        return f(self)
    def toSExp(self):
        tok = Token(unkpos, repr(self))
        return tok

class VarExp(AtomicExp):
    """A variable.

    @type name: String
    @param name: The name of the variable
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.name)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

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

# these may be useful synonyms
true = BoolExp(True)
false = BoolExp(False)

class VoidExp(AtomicExp):
    """void/nil/etc..."""
    def __repr__(self):
        return pretty(self.toSExp())
    def toSExp(self):
        sexp = SExp(unkpos, Token(unkpos, 'void'))
        return sexp

void = VoidExp()

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
    n = 1
    """A lambda expression.

    @type argExps: A List of VarExps
    @param argExps: The formal parameters of the lambda
    @type bodyExp: Any Scheme expression
    @param bodyExp: The body of the lambda
    """
    def __init__(self, argExps, bodyExp):
        if isinstance(argExps, AppExp):
            argExps = argExps.tolist()
        self.argExps = argExps
        self.bodyExp = bodyExp
        self.name = 'lambda_%d' % LamExp.n
        LamExp.n += 1

    def map(self, f):
        lam = LamExp([v.map(f) for v in self.argExps], self.bodyExp.map(f))
        lam.name = self.name
        return f(lam)

    def __repr__(self):
        return pretty(self.toSExp())

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'lambda'),
            SExp(unkpos, *[e.toSExp() for e in self.argExps]),
            self.bodyExp.toSExp()
            )
        return sexp

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

    def map(self, f):
        return f(AppExp(self.funcExp.map(f), *[exp.map(f) for exp in self.argExps]))

    def __repr__(self):
        return pretty(self.toSExp())

    def tolist(self):
        lst = [self.funcExp]
        lst.extend(self.argExps)
        return lst

    def toSExp(self):
        sexp = SExp(unkpos,
            self.funcExp.toSExp(),
            *[e.toSExp() for e in self.argExps]
            )
        return sexp

class IfExp:
    """An if expression.

    All three parameters can be any Scheme expression.
    """
    def __init__(self, condExp, thenExp, elseExp):
        self.condExp = condExp
        self.thenExp = thenExp
        self.elseExp = elseExp

    def map(self, f):
        return f(IfExp(self.condExp.map(f), self.thenExp.map(f), self.elseExp.map(f)))

    def __repr__(self):
        return pretty(self.toSExp())

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'if'),
            self.condExp.toSExp(),
            self.thenExp.toSExp(),
            self.elseExp.toSExp()
            )
        return sexp

class LetRecExp:
    """A letrec expression.

    @type bindings: A list of [VarExp, LamExp] bindings
    @param bindings: The bindings to add
    @type bodyExp: Any Scheme expression
    @param bodyExp: The body of the LetRec expression
    """
    def __init__(self, bindings, bodyExp):
        if isinstance(bindings, AppExp):
            bindings = bindings.tolist()
        for i, expr in enumerate(bindings):
            if isinstance(expr, AppExp):
                bindings[i] = expr.tolist()
        self.bindings = bindings
        self.bodyExp = bodyExp

    def map(self, f):
        return f(
            LetRecExp(
                [(v.map(f), l.map(f)) for v, l in self.bindings],
                self.bodyExp.map(f)
                )
            )

    def __repr__(self):
        return pretty(self.toSExp())

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'letrec'),
            SExp(unkpos, *[
                SExp(unkpos,
                    v.toSExp(),
                    f.toSExp()
                    ) for v, f in self.bindings
                ]),
            self.bodyExp.toSExp()
            )
        return sexp

class BeginExp:
    """A begin expression.

    @type exps: A list of Scheme expressions
    @param exps: The expressions contained within the `begin`
    """
    def __init__(self, *exps):
        self.exps = exps

    def map(self, f):
        return f(BeginExp(e.map(f) for e in self.exps))

    def __repr__(self):
        return pretty(self.toSExp())

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'begin'),
            SExp(unkpos, *[e.toSExp() for e in self.exps])
            )
        return sexp

class SetExp:
    """A set! expression.

    @type varExp: A VarExp
    @param varExp: The symbol to be rebound
    @type exp: Any Scheme expression
    @param exp: The new value to be bound to varExp
    """
    def __init__(self, varExp, exp):
        self.varExp = varExp
        self.exp = exp

    def map(self, f):
        return f(SetExp(self.varExp.map(f), self.exp.map(f)))

    def __repr__(self):
        return pretty(self.toSExp())

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'set!'),
            self.varExp.toSExp(),
            self.exp.toSExp()
            )
        return sexp

class SetThenExp:
    """A set-then! expression.

    @type varExp: A VarExp
    @param varExp: The symbol to be rebound
    @type exp: Any Scheme expression
    @param exp: The new value to be bound to varExp
    @type thenExp: Any Scheme expression
    @param thenExp: The continuation to apply
    """
    def __init__(self, varExp, exp, thenExp):
        self.varExp = varExp
        self.exp = exp
        self.thenExp = thenExp

    def map(self, f):
        return f(
            SetThenExp(
                self.varExp.map(f),
                self.exp.map(f),
                self.thenExp.map(f)
                )
            )

    def __repr__(self):
        pretty(self.toSExp())

    def toSExp(self):
        sexp = SExp(unkpos,
            Token(unkpos, 'set-then!'),
            self.varExp.toSExp(),
            self.exp.toSExp(),
            self.thenExp.toSExp()
            )
        return sexp
