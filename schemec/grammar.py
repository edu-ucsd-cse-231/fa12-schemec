import re

from types import (
    SExp,
    Token,
    BoolExp,
    NumExp,
    StrExp,
    LamExp,
    IfExp,
    LetRecExp
    )

__all__ = [
    'is_kwd',
    'is_bool',
    'is_integer',
    'is_decimal',
    'is_string',
    'is_identifier',
    'kwd_specs',
    'val_specs'
    ]


################################################################################
## Expression keywords
################################################################################

quote_kwd = 'quote'
lambda_kwd = 'lambda'
if_kwd = 'if'
set_kwd = 'set!'
begin_kwd = 'begin'
cond_kwd = 'cond'
and_kwd = 'and'
or_kwd = 'or'
case_kwd = 'case'
let_kwd = 'let'
lets_kwd = 'let*'
letrec_kwd = 'letrec'
do_kwd = 'do'
delay_kwd = 'delay'
quasiquote_kwd = 'quasiquote'

expression_kwds = [
    quote_kwd,
    lambda_kwd,
    if_kwd,
    set_kwd,
    begin_kwd,
    cond_kwd,
    and_kwd,
    or_kwd,
    case_kwd,
    let_kwd,
    lets_kwd,
    letrec_kwd,
    do_kwd,
    delay_kwd,
    quasiquote_kwd
    ]

################################################################################
## Syntactic keywords
################################################################################

else_kwd = 'else'
arrow_kwd = '=>'
define_kwd = 'define'
unquote_kwd = 'unquote'
unquote_splicing_kwd = 'unquote-splicing'

syntactic_kwds = expression_kwds + [
    else_kwd,
    arrow_kwd,
    define_kwd,
    unquote_kwd,
    unquote_splicing_kwd
    ]


################################################################################
## Regular expressions for matching grammar tokens
################################################################################

def is_token(tok):
    return isinstance(tok, Token)

re_kwd = re.compile(r'(?:{0})'.format('|'.join(syntactic_kwds)), re.I)
def is_kwd(tok):
    return True if is_token(tok) and re_kwd.match(tok.val) else False

re_bool = re.compile(r'#[tf]', re.I)
def is_bool(tok):
    return True if is_token(tok) and re_bool.match(tok.val) else False

re_integer = re.compile(r'[0-9]+', re.I)
def is_integer(tok):
    return True if is_token(tok) and re_integer.match(tok.val) else False

re_decimal = re.compile(r'(?:[0-9]+(?:\.[0-9]+)?(?:[esfdl][+-][0-9]+)?)', re.I)
def is_decimal(tok):
    return True if is_token(tok) and re_decimal.match(tok.val) else False

re_string = re.compile(r'"(?:[^"\\]|\\\\|\\")*"', re.I)
def is_string(tok):
    return True if is_token(tok) and re_string.match(tok.val) else False

initial = r'[a-z]|[!$%&*/:<=>?^_~]'
subsequent = r'{0}|[0-9]|[+-.@]'.format(initial)
re_identifier = re.compile(r'(?:(?:{0})(?:{1})*|(?:[+-]|...))'.format(initial, subsequent), re.I)
def is_identifier(tok):
    return True if is_token(tok) and re_identifier.match(tok.val) else False

kwd_specs = [
    ('lambda', 2, LamExp),
    ('if', 3, IfExp),
    ('letrec', 2, LetRecExp)
    ]

def to_bool(val):
    if val == '#t':
        return BoolExp(True)
    elif val == '#f':
        return BoolExp(False)
    else:
        raise ValueError('invalid Boolean: ' + str(val))

val_specs = [
    (is_bool, to_bool),
    (is_integer, NumExp),
    (is_decimal, NumExp),
    (is_string, StrExp)
    ]


################################################################################
## Grammar types
################################################################################

# class Grammar:
#     __slots__ = ('pos', 'val')
#
# class Variable(Grammar):
#     def __init__(self, tok):
#         if is_identifier(tok):
#             self.pos, self.val = tok
#         else:
#             return None

