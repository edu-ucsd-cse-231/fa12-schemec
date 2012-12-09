
import re

from textwrap import dedent

from schemec.typs import (
    Pos,
    SExp,
    Token
    )

NEWLINE = '\n'
WHITESPACE = ' \t\r\n'
LPAR = '('
RPAR = ')'
PAREN = LPAR + RPAR

def tokenize(txt):
    col = 1
    line = 1
    i = 0
    tokens = []
    # strip comments
    comments = re.compile(r';[^\n]*')
    txt = comments.sub('', txt)
    # tokenize
    for j, c in enumerate(txt):
        # handle delimiters
        if c in PAREN or c in WHITESPACE:
            # add tokens to the stream
            if i != j:
                tokens.append(Token(Pos(line, col - (j - i)), txt[i:j]))
            # add paren tokens and handle cursor position
            if c in PAREN:
                tokens.append(Token(Pos(line, col), c))
                col += 1
            elif c == NEWLINE:
                col = 1
                line += 1
            else:
                col += 1
            i = j + 1
        # handle regular characters
        else:
            col += 1
    return tokens

def parse(txt):
    stack = [[]]
    for token in tokenize(txt):
        if token.val == LPAR:
            stack.append(SExp(token.pos))
        elif token.val == RPAR:
            sexp = stack.pop()
            stack[-1].append(sexp)
        else:
            stack[-1].append(token)
    while not isinstance(stack, SExp):
        if len(stack) != 1:
            raise ValueError('invalid stack: '+ str(stack))
        stack = stack.pop()
    return stack

def simplify(expr):
    if isinstance(expr, SExp) and len(expr):
        if len(expr) == 1 and isinstance(expr[0], SExp):
            return simplify(expr[0])
        else:
            return SExp(expr.pos, [simplify(e) for e in expr])
    elif isinstance(expr, (SExp, Token)):
        return expr
    else:
        raise ValueError('invalid SExp: ' + str(expr))


def pretty(expr):
    subexpr = SExp
    # helper function for determining if some of an expr are expr
    def any_subexpr(expr):
        if not isinstance(expr, subexpr):
            return False
        else:
            return any(isinstance(e, subexpr) for e in expr)
    # helper function for determining if all of an expr are expr
    def all_subexpr(expr):
        if not isinstance(expr, subexpr):
            return False
        else:
            return all(isinstance(e, subexpr) for e in expr)
    # helper function for determining if we should split
    def partial_(expr):
        return (
            isinstance(expr, subexpr) and
            not all_subexpr(expr) and
            any_subexpr(expr) and
            len(expr) > 2
            )
    def pretty_(expr, indent, partial=False):
        prefix = NEWLINE + (' ' * 2 * indent)
        res = ''
        if isinstance(expr, subexpr):
            all_ = all_subexpr(expr)
            any_ = any_subexpr(expr)
            if not partial:
                res += LPAR
            if all_:
                prefix += ' ' * 2
                if not partial:
                    indent += 1
                    res = prefix + LPAR
                res += prefix.join(pretty_(e, indent) for e in expr)
            elif any_:
                res += ' '.join(pretty_(e, indent) for e in expr[:2])
                if len(expr) > 2:
                    res += NEWLINE + (' ' * 2 * (indent + 1))
                    res += pretty_(expr[2:], indent + 1, True)
            else:
                res += ' '.join(pretty_(e, indent) for e in expr)
            if not partial:
                res += RPAR
        elif isinstance(expr, Token):
            res += expr.val
        else:
            raise ValueError('invalid SExp: ' + str(expr))
        return res
    return pretty_(expr, 0)

if __name__ == '__main__':
    fac = dedent('''\
    ;; factorial : number -> number
    ;; to calculate the product of all positive
    ;; integers less than or equal to n.
    (define ((factorial n))
      (if (= n 0)
        1
        (* n (factorial (- n 1)))))
    ''')
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
