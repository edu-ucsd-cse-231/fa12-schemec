
import re

from pypeg2 import *

from .character import Character

class Comment:
    grammar = ';', restline, endl

class Atmosphere:
    grammar = some([whitespace, Comment])



class Expression:
    grammar = some([])


class Function:
    grammar = '(',
