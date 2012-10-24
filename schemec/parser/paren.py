
__all__ = ['paren']

def paren(*args):
    args.insert(0, '(')
    args.append(')')
    return tuple(args)
