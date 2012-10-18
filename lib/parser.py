#!/usr/bin/env python3

# CONSTANTS

class Const(object):
    OPEN = '('
    CLOSE = ')'
    DEF = 'define'
    LAM = 'lambda'
    LET = 'let'
    LETSEQ = 'let*'
    LETREC = 'letrec'

# EXPRESSIONS

class Expr(object):
    kwd, nargs = None, ()
    sugar = 0

class Lit(Expr):
    kwd = Const.LIT
    nargs = (0,)

class Def(Expr):
    kwd = Const.DEF
    nargs = (2,)

class Lam(Expr):
    kwd = Const.LAM
    nargs = (2,)

class Let(Expr):
    kwd = Const.LET
    nargs = (2, 3)
    sugar = 1

class Letseq(Expr):
    kwd = Const.LETSEQ
    nargs = (2,)
    sugar = 2

class Letrec(Expr):
    kwd = Const.LETREC
    nargs = (2,)
    sugar = 2

# PARSING

class Parser(object):
    pass

class ExprParser(Parser):
    UNK, LIT, DEF, LAM, LET, LETSEQ, LETREC = range(7)
    def __init__(self):
        self.state = ExprParser.UNK

    def __tokenize(self, string):
        toks = []
        oidx = string.find(Const.OPEN)
        if odix >= 0:
            if odix > 0:
                toks.append(string[0:oidx])
            cidx = string.rfind(Const.CLOSE)
            toks.append(string[odix + 1:cidx])

    def __call__(self, string):


def parse(string):
    parser = ExprParser()

