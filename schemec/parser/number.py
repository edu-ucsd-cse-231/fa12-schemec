
import re

from pypeg2 import maybe_some, optional, some

__all__ = ['Number']

class Exponent:
    grammar = re.compile(r'[esfdl]', re.I)

sign = re.compile(r'[+-]')
class Sign:
    grammar = optional(sign)

class Exactness:
    grammar = optional(re.compile(r'#[ie]', re.I))

class Radix2:
    grammar = re.compile(r'#b', re.I)

class Radix8:
    grammar = re.compile(r'#o', re.I)

class Radix10:
    grammar = optional(re.compile(r'#d', re.I))

class Radix16:
    grammar = re.compile(r'#x', re.I)

class Digit2:
    grammar = re.compile(r'[01]')

class Digit8:
    grammar = re.compile(r'[0-7]')

class Digit10:
    grammar = re.compile(r'[0-9]')

class Digit16:
    grammar = re.compile(r'[0-9a-f]', re.I)

class Suffix:
    grammar = optional((Exponent, Sign, some(Digit10)))

imaginary = re.compile(r'i', re.I)

# store the generated classes in d,
# which we will use to update locals with
num_classes = {}

for base in [2, 8, 10, 16]:
    radix = locals()['Radix%d' % base]
    digit = locals()['Digit%d' % base]

    class Prefix_:
        grammar = [
            (radix, Exactness),
            (Exactness, radix)
            ]
    num_classes['Prefix%d' % base] = Prefix_

    class UInteger_:
        grammar = some(digit), '#*'
    num_classes['UInteger%d' % base] = UInteger_

    class UReal_:
        grammar = [
            UInteger_,
            (UInteger_, '/', UInteger_)
            ]
    num_classes['UReal%d' % base] = UReal_

    class Real_:
        grammar = Sign, UReal_
    num_classes['Real%d' % base] = Real_

    class Complex_:
        grammar = [
            Real_,
            (Real_, '@', Real_),
            (Real_, sign, optional(UReal_), imaginary),
            (sign, UReal_, imaginary),
            (sign, imaginary)
            ]
    num_classes['Complex%d' % base] = Complex_

    class Num_:
        grammar = Prefix_, Complex_
    num_classes['Num%d' % base] = Num_

locals().update(num_classes)

class Decimal10:
    grammar = [
        (UInteger10, Suffix),
        ('.', some(Digit10), '#*', Suffix),
        (some(Digit10), '.', maybe_some(Digit10), '#*', Suffix),
        (some(Digit10), '#+', '.', '#*', Suffix)
        ]

# don't forget to add Decimal10 to UReal10
UReal10.grammar.append(Decimal10)

class Number:
    grammar = [Num2, Num8, Num10, Num16]
