
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
    """
    throw an error message
    @type msg: a string
    @param msg: string containing the error message
    """
    print('error:', msg, file=stderr)

def unimplemented(expr):
    """
    throw an unimplemented error"
    @type expr: a SExp or Token
    @param expr: SExp or Token which we haven't implemented
    """
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
    """
    throw a wrong-number-of-arguments error
    @type narg: an integer
    @param narg: the correct number of arguments
    @type expr: a SExp or Token
    @param expr: the SExp or Token which threw the wrong # of args error
    """
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
    """
    throw an invalid variable name error
    @type expr: a Token
    @param expr: a token with an invalid val for variable naming
    """
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
            rest = [to_exp(e) for e in tail]
            name = head.val
            if is_kwd(head):
                name = name.lower()
                try:
                    narg, init = next((narg, f) for n, narg, f in kwd_specs if n == name)
                    if len(expr[1:]) != narg:
                        wrong_nargs(narg, expr)
                    return init(*rest) if all(rest) else None
                except StopIteration:
                    return unimplemented(expr)
            else:
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
    evenodd = dedent('''\
    (letrec ((even?
              (lambda (n)
                (if (zero? n)
                    #t
                    (odd? (- n 1)))))
             (odd?
              (lambda (n)
                (if (zero? n)
                    #f
                    (even? (- n 1))))))
      (even? 88))
    ''')
    print(parse(evenodd))
    print(pretty(parse(evenodd)))
    print(ast(evenodd))
