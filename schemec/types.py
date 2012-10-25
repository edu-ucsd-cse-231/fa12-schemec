from collections import namedtuple


################################################################################
## Scheme Expressions
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
    def __init__(self, funcExp, *argExps):
        self.funcExp = funcExp
        self.argExps = argExps

    def __repr__(self):
        return '({0} {1})'.format(self.funcExp,
                                  ' '.join(map(str, self.argExps)))


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
        # f = exp.funcExp
        # es = exp.argExps
        # _rv = gensym('$rv')
        # cont = LamExp([_rv], k(_rv))
        # return T_k(f, lambda _f:
        #                   T_k(*es, lambda _e:
        #                             AppExp(_f, _e, cont)))
        _rv = gensym('$rv')
        cont = LamExp([_rv], k(_rv))
        T_c(exp, cont)
    else:
        raise TypeError(exp, k)

def T_c(exp, c):
    if isinstance(exp, VarExp):
        return AppExp(c, M(exp))
    elif isinstance(exp, LamExp):
        return AppExp(c, M(exp))
    elif isinstance(exp, AppExp):
        f = exp.funcExp
        es = exp.argExps
        return T_k(f, lambda _f:
                   Tx_k(es, lambda _es:
                        AppExp(_f, *(_es + [c]))))
    else:
        raise TypeError(exp, c)

def Tx_k(exps, k):
    if len(exps) == 0:
        return k([])
    else:
        return T_k(exps[0],
                   lambda hd: Tx_k(exps[1:],
                                   lambda tl: k([hd] + tl)))

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


################################################################################
## Main
################################################################################

if __name__ == '__main__':
    exp = AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')),
                 VarExp('a'),
                 VarExp('b'))
    print(exp)
    print(T_c(exp, VarExp('halt')))
