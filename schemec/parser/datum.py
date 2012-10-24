
from pypeg2 import maybe_some, some

from .basetype import *

__all__ = ['Datum']

# delay until after Datum has been defined
class List:
    grammar = None

class Vector:
    grammar = None

class SimpleDatum:
    grammar = some([Boolean, Number, Character, String, Symbol])

class CompoundDatum:
    grammar = [List, Vector]

class Datum:
    grammar = some([SimpleDatum, CompoundDatum])

class Abbreviation:
    grammar = re.compile(r"(?:'|`|,|,@)"), Datum

# handle circular dependency between list and vector
List.grammar = [
    paren(maybe_some(Datum)),
    paren(some(Datum), '.', Datum),
    Abbreviation
    ]

Vector.grammar = '#(', maybe_some(Datum), ')'

