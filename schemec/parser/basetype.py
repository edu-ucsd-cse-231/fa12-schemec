
from pypeg2 import maybe_some, some

from .character import *
from .number import *

__all__ = [
    'Boolean',
    'Character',
#     'Keyword',
    'Number',
    'String',
    'Symbol',
    ]

delimiter = re.compile(r'(?:\s|\||"|;)')
digit = re.compile(r'[0-9]')
letter = re.compile(r'[a-z]', re.I)
special_initial = re.compile(r'[!$%&*/:<=>?^_~]')
special_subsequent = re.compile(r'[+-.@]')
peculiar_identifier = re.compile(r'(?:\+|-|...)')

class Boolean:
    grammar = re.compile(r'#[tf]', re.I)

class Initial:
    grammar = [letter, special_initial]

class Subsequent:
    grammar = [Initial, digit, special_subsequent]

class Identifier:
    grammar = [Initial, maybe_some(Subsequent)], peculiar_identifier

class String:
    grammar = '"', some([r'\"', r'\\', re.compile(r'[^\"]')]), '"'

Symbol = Identifier

# this is used by Macro,
# which I'm not implementing
# Keyword = Identifier
