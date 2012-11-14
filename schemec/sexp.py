
import re

from textwrap import dedent

from types import (
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

def has_subexpr(expr):
    if not isinstance(expr, SExp):
        return False
    else:
        return any(isinstance(e, SExp) for e in expr)

def pretty(expr, indent=0):
    prefix = ' ' * indent
    res = prefix
    if isinstance(expr, SExp):
        res += LPAR
        if has_subexpr(expr):
            res += ' '.join(pretty(e) for e in expr[:2])
            if len(expr) > 2:
                res += NEWLINE
                res += pretty(expr[2:], indent + 1)
        else:
            res += ' '.join(pretty(e) for e in expr)
        res += RPAR
    elif isinstance(expr, Token):
        res += expr.val
    elif isinstance(expr, list):
        res += (NEWLINE + prefix).join(pretty(e, indent) for e in expr)
    return res

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
    (letrec fact
      (lambda (x)
        (if (= x 0)
          1
          (* x (fact (- x 1)))))
      (fact 5))
    ''')
    print(parse(fac5))
    print(pretty(parse(fac5)))
