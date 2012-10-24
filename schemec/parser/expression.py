
from pypeg2 import maybe_some, optional, some

from .basetype import Boolean, Number, Character, String
from .datum import Datum
from .paren import paren

syntactic_kwds = [
    'else',
    '=>',
    'define',
    'unquote',
    'unquote-splicing'
    ]

class SyntacticKeyword:
    grammar = re.compile('(?:%s)' % '|'.join(syntactic_kwds), re.I)

expression_kwds = [
    'quote',
    'lambda',
    'if',
    'set!',
    'begin',
    'cond',
    'and',
    'or',
    'case',
    'let',
    'let\\*',
    'letrec',
    'do',
    'delay',
    'quasiquote'
    ]

class ExpressionKeyword:
    grammar = re.compile('(?:%s)' % '|'.join(expression_kwds), re.I)

kwds = syntactic_kwds + expression_kwds

class Variable:
    grammar = re.compile('(?!%s).+' % '|'.join('^%s$' % kwd for kwd in kwds), re.I)

class Quotation:
    grammar = [
        ("'", Datum),
        paren('quote', Datum)
        ]

class SelfEvaluating:
    grammar = [Boolean, Number, Character, String]

class Literal:
    grammar = [Quotation, SelfEvaluating]

class Operator:
    grammar = None

class Operand:
    grammar = None

class ProcedureCall:
    grammar = paren(Operator, maybe_some(Operand))

class Formals:
    grammar = [
        paren(maybe_some(Variable)),
        Variable,
        (some(Variable), '.', Variable)
        ]

class DefFormals:
    grammar = [
        maybe_some(Variable),
        (maybe_some(Variable), '.', Variable)
        ]

class Definition:
    grammar = None

class Command:
    grammar = None

class Sequence:
    grammar = None

class Body:
    grammar = maybe_some(Definition), Sequence

lambda_kwd = re.compile('lambda', re.I)
class LambdaExpression:
    grammar = paren(lambda_kwd, Formals, Body)

class Test:
    grammar = None

class Consequent:
    grammar = None

class Alternate:
    grammar = None

if_kwd = re.compile(r'if', re.I)
class Conditional:
    grammar = paren(if_kwd, Test, Consequent, Alternate)

class Assignment:
    grammar = None

class DerivedExpression:
    grammar = None # do we really need this???

# do we really want Macros?
# class MacroUse:
#     grammar = '(', Keyword, maybe_some(Datum), ')'
#
# class MacroBlock:
#     grammar =

class Expression:
    grammar = [
        Variable,
        Literal,
        ProcedureCall,
        LambdaExpression,
        Conditional,
        Assignment,
        DerivedExpression
#         MacroUse,
#         MacroBlock
        ]

# For every grammar = None above, there
# should be an entry here using Expression

Operator.grammar = Expression

Operand.grammar = Expression

begin_kwd = re.compile('begin', re.I)
define_kwd = re.compile('define', re.I)
Definition.grammar = [
    paren(define_kwd, Variable, Expression),
    paren(define_kwd, '(', Variable, DefFormals, ')', Body),
    paren(begin_kwd, maybe_some(Definition))
    ]

Command.grammar = Expression

Sequence.grammar = maybe_some(Command), Expression

Test.grammar = Expression

Consequent.grammar = Expression

Alternate.grammar = optional(Expression)

set_kwd = re.compile(r'set!', re.I)
Assignment.grammar = paren(set_kwd, Variable, Expression)

cond_kwd = re.compile('cond', re.I)
else_kwd = re.compile('else', re.I)
case_kwd = re.compile('case', re.I)
and_kwd = re.compile('and', re.I)
or_kwd = re.compile('or', re.I)
let_kwd = re.compile('let', re.I)
lets_kwd = re.compile(r'let\*', re.I)
letrec_kwd = re.compile('letrec', re.I)
do_kwd = re.compile('do', re.I)
delay_kwd = re.compile('delay', re.I)
DerivedExpression.grammar = [
    paren(cond_kwd, some(CondClause)),
    paren(cond_kwd, maybe_some(CondClause), '(', else_kwd, Sequence, ')'),
    paren(case_kwd, Expression, some(CaseClause)),
    paren(case_kwd, Expression, maybe_some(CaseClause), '(', else_kwd, Sequence, ')'),
    paren(and_kwd, maybe_some(Test)),
    paren(or_kwd, maybe_some(Test)),
    paren(let_kwd, '(', maybe_some(BindingSpec), ')', Body),
    paren(let_kwd, Variable, '(', maybe_some(BindingSpec), ')', Body),
    paren(lets_kwd, '(', maybe_some(BindingSpec), ')', Body),
    paren(letrec_kwd, '(', maybe_some(BindingSpec), ')', Body),
    paren(begin_kwd, Sequence),
    paren(do_kwd, '(', maybe_some(IterationSpec), ')', '(', Test, DoResult, ')', )
    ]
