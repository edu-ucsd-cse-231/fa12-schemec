
from sys import stderr
from textwrap import dedent

from grammar import (
    is_kwd,
    is_identifier,
    kwd_specs,
    val_specs
    )
from sexp import SExp, parse, pretty
from types import (
    VarExp,
    NumExp,
    BoolExp,
    StrExp,
    LamExp,
    AppExp,
    IfExp,
    LetRecExp
    )

def error(msg):
    print('error:', msg, file=stderr)

def unimplemented(expr):
    if isinstance(expr, SExp):
        error("unimplemented expression (line: {0}, col: {1}): '({2} ...)'".format(
                expr.pos.line,
                expr.pos.col,
                expr[0].val
                )
            )
    else:
        error("unimplemented value (line: {0}, col: {1}: '{2}'".format(
                expr.pos.line,
                expr.pos.col,
                expr[0].val
                )
            )
    return None

def wrong_nargs(narg, expr):
    error("incorrect number of arguments ({0} != {1}) supplied to '{2}' (line: {3}, col: {4})".format(
            len(expr) - 1,
            narg,
            expr[0].val,
            expr.pos.line,
            expr.pos.col
            )
        )
    return None

def invalid_varname(expr):
    error("invalid variable name '{0}' (line: {1}, col: {2})".format(
            expr.val,
            expr.pos.line,
            expr.pos.col
            )
        )
    return None

def to_exp(expr):
    if isinstance(expr, SExp):
        if isinstance(expr[0], SExp):
            return [to_exp(e) for e in expr]
        else:
            head = expr[0]
            tail = expr[1:]
            name = head.val
            if is_kwd(head):
                name = name.lower()
                try:
                    if name == 'letrec':
                        rest = [to_exp(e) for e in tail[0][0]] + [to_exp(e) for e in tail[1:]]
                    else:
                        rest = [to_exp(e) for e in tail]
                    narg, init = next((narg, f) for n, narg, f in kwd_specs if n == name)
                    if len(expr[1:]) != narg:
                        wrong_nargs(narg, expr)
                    return init(*rest) if all(rest) else None
                except StopIteration:
                    return unimplemented(expr)
            else:
                rest = [to_exp(e) for e in tail]
                return AppExp(VarExp(name), *rest) if all(rest) else None
    else:
        try:
            init = next(f for t, f in val_specs if t(expr))
            return init(expr.val)
        except StopIteration:
            if is_identifier(expr):
                if is_kwd(expr):
                    return invalid_varname(expr)
                else:
                    return VarExp(expr.val)
            else:
                return unimplemented(expr)

def ast(txt):
    return to_exp(parse(txt))

if __name__ == '__main__':
    fac5 = dedent('''\
    ;; factorial : number -> number
    ;; to calculate the product of all positive
    ;; integers less than or equal to n.
    (letrec ((fact
      (lambda (x)
        (if (= x 0)
          1
          (* x (fact (- x 1)))))))
      (fact 5))
    ''')
    print(parse(fac5))
    print(pretty(parse(fac5)))
    print(ast(fac5))
