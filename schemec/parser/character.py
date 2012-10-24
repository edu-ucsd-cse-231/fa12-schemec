
from pypeg2 import some

__all__ = ['Character']

class Space:
    grammar = re.compile(r'space', re.I)

class Linefeed:
    grammar = re.compile(r'(?:linefeed)', re.I)

class Newline:
    grammar = re.compile(r'(?:newline)', re.I)

class Meta:
    grammar = re.compile(r'm(?:eta)-', re.I)

class Control:
    grammar = re.compile(r'c(?:ontrol)-', re.I)

class Super:
    grammar = re.compile(r's(?:uper)-', re.I)

class Hyper:
    grammar = re.compile(r'h(?:yper)-', re.I)

class Top:
    grammar = re.compile(r't(?:op)-', re.I)

ascii_chars = [
    'NUL',
    'SOH',
    'STX',
    'ETX',
    'EOT',
    'ENQ',
    'ACK',
    'BEL',
    'BS',
    'HT',
    'LF',
    'VT',
    'FF',
    'CR',
    'SO',
    'SI',
    'DLE',
    'DC1',
    'DC2',
    'DC3',
    'DC4',
    'NAK',
    'SYN',
    'ETB',
    'CAN',
    'EM',
    'SUB',
    'ESC',
    'FS',
    'GS',
    'RS',
    'US',
    'DEL'
    ]

class Ascii:
    grammar = re.compile('(?:%s)' % '|'.join(ascii_chars), re.I)

class CharacterName:
    grammar = [Space, Linefeed, Newline, Meta, Control, Super, Hyper, Top, Ascii]

class Character:
    # can't use r'' syntax or it breaks vim's coloring...annoying
    grammar = '#\\', some((CharacterName, re.compile(r'.')))
