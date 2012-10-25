from collections import namedtuple


################################################################################
## Regular Scheme Expressions
################################################################################

# VarExp = namedtuple('VarExp', 'val')
# LamExp = namedtuple('LamExp', 'var, bodyExp')
# AppExp = namedtuple('AppExp', 'funcExp, argExp')
# IfExp  = namedtuple('IfExp',  'condExp, thenExp, elseExp')

class VarExp:
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return str(self.val)

class LamExp:
    def __init__(self, vars, bodyExp):
        self.vars = vars
        self.bodyExp = bodyExp

    def __repr__(self):
        return '(lambda ({0}) {1})'.format(' '.join(map(str, self.vars)),
                                           self.bodyExp)

class AppExp:
    def __init__(self, funcExp, argExp):
        self.funcExp = funcExp
        self.argExp = argExp

    def __repr__(self):
        return '({0} {1})'.format(self.funcExp, self.argExp)


################################################################################
## CPS Scheme Expressions
################################################################################

# Vars and Lambdas don't change in CPS
class AppExpC:
    def __init__(self, funcExp, *argExps):
        self.funcExp = funcExp
        self.argExps = argExps

    def __repr__(self):
        return '({0} {1})'.format(self.funcExp, ' '.join(map(str, self.argExps)))
# AppExpC = namedtuple('AppExpC', 'funcExp, argExps')
# IfExpC  = namedtuple('IfExpC',  'condExp, thenExp, elseExp')


################################################################################
## Conversion to CPS
################################################################################

class GenSym:
    n = 1
    def __call__(self, sym):
        sym += str(self.n)
        self.n += 1
        return VarExp(sym)
gensym = GenSym()

def T_k(exp, k):
    if isinstance(exp, VarExp):
        return k(M(exp))
    elif isinstance(exp, LamExp):
        return k(M(exp))
    elif isinstance(exp, AppExp):
        f = exp.funcExp
        e = exp.argExp
        _rv = gensym('$rv')
        cont = LamExp([_rv], k(_rv))
        return T_k(f, lambda _f:
                          T_k(e, lambda _e:
                                    AppExpC(_f, _e, cont)))
    else:
        raise TypeError(exp, k)

def T_c(exp, c):
    if isinstance(exp, VarExp):
        return AppExp(c, M(exp))
    elif isinstance(exp, LamExp):
        return AppExp(c, M(exp))
    elif isinstance(exp, AppExp):
        f = exp.funcExp
        e = exp.argExp
        return T_k(f, lambda _f:
                   T_k(e, lambda _e:
                       AppExpC(_f, _e, c)))
    else:
        raise TypeError(exp, c)

def M(exp):
    if isinstance(exp, VarExp):
        return exp
    elif isinstance(exp, LamExp):
        vars = exp.vars
        body = exp.bodyExp
        _k = gensym('$k')
        return LamExp(vars + [_k],
                      T_c(body, _k))
    else:
        raise TypeError(exp)
