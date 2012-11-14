
from types import *

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
    """Transform an expression into CPS with a continuation lifted into the host
    language.

    @type exp: A Scheme expression
    @param exp: The expression to transform
    @type k: A *Python* function from SchemeExp -> SchemeExp
    @param k: The continuation to apply
    """
    if isinstance(exp, AtomicExp):
        return k(M(exp))
    elif isinstance(exp, AppExp):
        _rv = gensym('$rv')
        cont = LamExp([_rv], k(_rv))
        return T_c(exp, cont)
    elif isinstance(exp, IfExp):
        ce = exp.condExp
        te = exp.thenExp
        ee = exp.elseExp
        return T_k(ce, lambda _ce: IfExp(_ce, T_k(te, k), T_k(ee, k)))
    else:
        raise TypeError(exp)

def T_c(exp, c):
    """Transform an expression into CPS.

    @type exp: A Scheme expression
    @param exp: The expression to transform
    @type c: LamExp
    @param c: The continuation to apply
    """
    if isinstance(exp, AtomicExp):
        return AppExp(c, M(exp))
    elif isinstance(exp, AppExp):
        f = exp.funcExp
        es = exp.argExps
        return T_k(f, lambda _f:
                   Tx_k(es, lambda _es:
                        AppExp(_f, *(_es + [c]))))
    elif isinstance(exp, IfExp):
        ce = exp.condExp
        te = exp.thenExp
        ee = exp.elseExp
        _k = gensym('$k')
        return AppExp(LamExp([_k], T_k(ce, lambda _ce:
                                       IfExp(_ce, T_c(te, _k), T_c(ee, _k)))),
                             c)
    elif isinstance(exp, LetRecExp):
        vfes = exp.varFuncExps
        be = exp.bodyExp
        return LetRecExp([ve, M(fe) for ve, fe in vfes], T_c(be, c))
    else:
        raise TypeError(exp)

def Tx_k(exps, k):
    """Transform a list of expressions into CPS.

    @type exps: A List of SchemeExps
    @type k: LamExp
    """
    if len(exps) == 0:
        return k([])
    else:
        return T_k(exps[0],
                   lambda hd: Tx_k(exps[1:],
                                   lambda tl: k([hd] + tl)))

def M(exp):
    """Transform an AtomicExp into CPS.

    @type exp: AtomicExp
    """
    if isinstance(exp, LamExp):
        vars = exp.vars
        body = exp.bodyExp
        _k = gensym('$k')
        return LamExp(vars + [_k],
                      T_c(body, _k))
    elif isinstance(exp, AtomicExp):
        return exp
    else:
        raise TypeError(exp)


################################################################################
## Main
################################################################################

if __name__ == '__main__':
    exp = AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')),
                 BoolExp(True),
                 BoolExp(False))
    print(exp)
    print(T_c(exp, VarExp('halt')))

    exp = IfExp(IfExp(BoolExp(True), BoolExp(False), BoolExp(True)), NumExp(1), NumExp(0))
    print(exp)
    print(T_c(exp, VarExp('halt')))

    exp = LetRecExp([[VarExp('fact'), LamExp([VarExp('x')],
                                           IfExp(AppExp(VarExp('='),
                                                        VarExp('x'),
                                                        NumExp(0)),
                                                 NumExp(1),
                                                 AppExp(VarExp('*'),
                                                        VarExp('x'),
                                                        AppExp(VarExp('fact'),
                                                               AppExp(VarExp('-'),
                                                                      VarExp('x'),
                                                                      NumExp(1))))))]],
                    AppExp(VarExp('fact'), NumExp(5)))
    print(exp)
    print(T_c(exp, VarExp('halt')))
