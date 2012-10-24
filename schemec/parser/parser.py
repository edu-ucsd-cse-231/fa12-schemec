#!/usr/bin/env python3

class C:
    OPEN = '('
    CLOSE = ')'

def tokenize(s):
    s.replace(C.OPEN, ' %s ' % C.OPEN).replace(C.CLOSE, ' %s ' % C.CLOSE).split()

def parse(tokens):

