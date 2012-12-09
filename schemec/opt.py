
from functools import partial

from schemec.typs import (
    AtomicExp,
    VarExp,
    AppExp,
    LamExp
    )


__all__ = [
    'optimize'
    ]


def substitute_vars(vars_dict, exp):
    if isinstance(exp, VarExp):
        return vars_dict.get(exp, exp)
    else:
        return exp

def inline(exp):
    # basic idea: AppExp(LamExp(), AtomExps) -> body of LamExp
    if (isinstance(exp, AppExp) and
        isinstance(exp.funcExp, LamExp) and
        all(isinstance(arg, AtomicExp) for arg in exp.argExps)):
        vars_dict = dict(zip(exp.funcExp.argExps, exp.argExps))
        ret = exp.funcExp.bodyExp.map(partial(substitute_vars, vars_dict))
        return ret
    else:
        return exp

def optimize(exp):
    opts = [
        inline
        ]
    for opt in opts:
        exp = exp.map(opt)
    return exp
