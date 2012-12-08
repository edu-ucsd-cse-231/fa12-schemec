
from functools import partial
from textwrap import dedent

from schemec.types import (
    AtomicExp,
    VarExp,
    NumExp,
    BoolExp,
    true,
    false,
    VoidExp,
    void,
    StrExp,
    LamExp,
    AppExp,
    IfExp,
    LetRecExp,
    BeginExp,
    SetExp,
    SetThenExp,
    gensym
    )

__all__ = [
    'gen_c',
    'halt',
    'pretty_C'
    ]

NUM, STR, CONT = 'NUM', 'STR', 'CONT'
TYPES = [NUM, STR, CONT]

class NumPrimOps:
    binary_fmt = '{dst}->num = {lhs}->num {op} {rhs}->num;'
    binary_ops = {
        '+': '+',
        '-': '-',
        '*': '*',
        '=': '=='
        }

    unary_fmt = '{dst}->num = {lhs}->num {op};'
    unary_ops = {
        'zero?': '== 0'
        }

    @staticmethod
    def __call__(op, dst, lhs, rhs=None):
        try:
            if rhs is None:
                op = NumPrimOps.unary_ops[op]
                return (NUM, NumPrimOps.unary_fmt.format(
                    dst=dst, lhs=lhs, op=op
                    ))
            else:
                op = NumPrimOps.binary_ops[op]
                return (NUM, NumPrimOps.binary_fmt.format(
                    dst=dst, lhs=lhs, op=op, rhs=rhs
                    ))
        except KeyError:
            raise RuntimeError('unimplemented primitive number operation: {0}'.format(str(op)))

    @staticmethod
    def __contains__(key):
        return (
            key in NumPrimOps.binary_ops or
            key in NumPrimOps.unary_ops
            )

    @staticmethod
    def __getitem__(key):
        if key in NumPrimOps.binary_ops:
            return NumPrimOps.binary_ops[key]
        elif key in NumPrimOps.unary_ops:
            return NumPrimOps.unary_ops[key]
        else:
            raise KeyError(key)

num_primops = NumPrimOps()

class StrPrimOps:
    binary_ops = {
        'string-append': dedent('''\
            {dst}->str = std::shared_ptr<std::string>({lhs}->str);
            {dst}->str.append({rhs}->str);'''
            ),
        'string=?': '{dst}->num = {lhs}->str.compare({rhs}->str) != 0;'
        }

    @staticmethod
    def __call__(op, dst, lhs, rhs=None):
        try:
            if rhs is None:
                raise KeyError(op)
            else:
                return (STR, StrPrimOps.binary_ops[op].format(
                    dst=dst, lhs=lhs, rhs=rhs
                    ))
        except KeyError:
            raise RuntimeError('unimplemented primitive operation: {0}'.format(str(op)))

    @staticmethod
    def __contains__(key):
        return key in StrPrimOps.binary_ops

    @staticmethod
    def __getitem__(key):
        if key in StrPrimOps.binary_ops:
            return StrPrimOps.binary_ops[key]
        else:
            raise KeyError(key)

str_primops = StrPrimOps()

def is_primop(op):
    if op in num_primops or op in str_primops:
        return True
    else:
        return False

def gen_primop(op, dst, *args):
    if op in num_primops:
        return num_primops(op, dst, *args)
    elif op in str_primops:
        return str_primops(op, dst, *args)
    else:
        raise KeyError(op)

def unimplemented(exp):
    raise RuntimeError('unimplemented expression type: {0}'.format(str(type(exp))))

def compute_holes(rootExp):
    holes_dict = {}
    def find_holes(holes, exp):
        if isinstance(exp, LamExp):
            holes_dict[exp] = holes - set(exp.argExps)
            holes -= set(exp.argExps)
        elif isinstance(exp, VarExp):
            if not is_primop(exp.name):
                holes.add(exp)
        return exp
    rootExp.map(partial(find_holes, set()))
    return holes_dict

class CCode:
    def __init__(self, typ, code, decls):
        self.typ = typ
        self.code = code
        self.decls = decls
    def __str__(self):
        return self.code
    def __repr__(self):
        return self.code

def declare(var):
    return 'std::unique_ptr<schemetype_t*> {0} (new schemetype_t);'.format(var)

halt = gensym('halt')

def gen_c(exp):
    # compute the holes at each LamExp
    holes = compute_holes(exp)

    # map function
    def to_c(nargs, exp):
        code = None

        decls = []

        if isinstance(exp, VarExp):
            if exp == halt:
                # don't forget to count the narg of our halt
                nargs.add(1)
                code = dedent('''\
                    [](std::unique_ptr<schemetype_t*> __halt_0) {{
                      {halt1}
                      __halt_1->num = 0;
                      __halt_1->type = {NUM};
                      switch(__halt_0->type) {{
                       case {NUM}:
                        printf("%ld\\n", __halt_0->num);
                       case {STR}:
                        printf("%s\\n", *(__halt_0->str));
                       case {CONT}:
                        printf("you want to return a lambda?! really?!\\n");
                       default:
                        printf("error\\n");
                        __halt_1->num = -1;
                      }}
                      return __halt_1;
                    }}''').format(
                        halt1=declare('__halt_1'),
                        NUM=NUM, STR=STR, CONT=CONT
                        )
            else:
                code = exp.name
        elif isinstance(exp, (NumExp, BoolExp, StrExp)):
            if isinstance(exp, NumExp):
                val = str(exp.val)
                sym = '__num_'
                typ = NUM
            elif isinstance(exp, BoolExp):
                val = '1' if exp.val else '0'
                sym = '__bool_'
                typ = NUM
            elif isinstance(exp, StrExp):
                val = '"{0}"'.format(exp.val)
                sym = '__str_'
                typ = STR
            else:
                assert(0)
            tmp = gensym(sym)
            decl = (
                declare(tmp),
                dedent('''\
                    {var}->{loc} = {val};
                    {var}->type = {typ};''').format(
                        var=tmp.name,
                        loc=typ.lower(),
                        val=val,
                        typ=typ.upper()
                        )
                )
            decls.append(decl)
            code = tmp.name
        elif isinstance(exp, VoidExp):
            unimplemented(exp)
        elif isinstance(exp, LamExp):
            # help compute the maximum number of arguments
            nargs.add(len(exp.argExps))
            tmp = gensym('__lam_')
            decls_, ops = zip(*exp.bodyExp.decls)
            decl = (
                declare(tmp),
                dedent('''\
                    {var}->cont._{narg} = [{holes}]({args}) -> std::unique_ptr<schemetype_t*> {{
                    {decls}
                    {ops}
                    return {body};
                    }}
                    {var}->type = CONT;''').format(
                        var=tmp.name,
                        narg=len(exp.argExps),
                        holes=', '.join(hole.name for hole in holes[exp]),
                        args=', '.join(
                            'std::unique_ptr<schemetype_t*> {0}'.format(str(arg))
                            for arg in exp.argExps
                            ),
                        decls='\n'.join(d for d in decls_ if d),
                        ops='\n'.join(ops),
                        body=str(exp.bodyExp)
                        )
                )
            decls.append(decl)
            code = tmp.name
        elif isinstance(exp, AppExp):
            for arg in exp.argExps:
                decls.extend(arg.decls)
            decls.extend(exp.funcExp.decls)
            tmp = gensym('__ret_')
            func = str(exp.funcExp)
            if is_primop(func):
                prim = gensym('__prim_')
                typ, body = gen_primop(func, prim, *[str(arg) for arg in exp.argExps[:-1]])
                decl = (
                    declare(prim) + '\n' + declare(tmp),
                    dedent('''\
                        {body}
                        {prim}->type = {typ};
                        {var} = {cont}->cont._1({prim});''').format(
                            prim=prim.name,
                            body=body,
                            typ=typ,
                            var=tmp.name,
                            cont=str(exp.argExps[-1])
                            )
                    )
                decls.append(decl)
            elif exp.funcExp.typ == VarExp:
                decl = (
                    '',
                    '{var} = {func}->cont._{narg}({args});'.format(
                        var=tmp.name,
                        func=str(exp.funcExp),
                        narg=len(exp.argExps),
                        args=', '.join(str(arg) for arg in exp.argExps)
                        )
                    )
                decls.append(decl)
            else:
                raise RuntimeError('AppExp unimplemented for funcExp of type: {0}'.format(str(exp.funcExp.typ)))
            code = tmp.name
        elif isinstance(exp, IfExp):
            decls.extend(exp.condExp.decls)
            decls.extend(exp.thenExp.decls)
            decls.extend(exp.elseExp.decls)
            code = '(({cond})->num) ? ({then}) : ({else_})'.format(
                cond=str(exp.condExp),
                then=str(exp.thenExp),
                else_=str(exp.elseExp)
                )
        elif isinstance(exp, LetRecExp):
            for var, body in exp.bindings:
                decls.extend(body.decls)
                decl = (
                    declare(var),
                    '{var} = {body};'.format(
                        var=str(var),
                        body=str(body)
                        )
                    )
                decls.append(decl)
            decls.extend(exp.bodyExp.decls)
            code = str(exp.bodyExp)
        elif isinstance(exp, BeginExp):
            unimplemented(exp)
        elif isinstance(exp, SetExp):
            unimplemented(exp)
        elif isinstance(exp, SetThenExp):
            unimplemented(exp)
        else:
            unimplemented(exp)
        return CCode(type(exp), code, decls)

    nargs = set()
    body = exp.map(partial(to_c, nargs))

    min_narg, max_narg = min(nargs), max(nargs)
    conttype = dedent('''\
        union {{
          {0}
        }} cont;''').format(
            '\n  '.join(
                'std::function<std::unique_ptr<schemetype_t*>({0})> _{1};'.format(
                    ', '.join('std::unique_ptr<schemetype_t*>' for _ in range(i)),
                    i
                    ) for i in range(min_narg, max_narg + 1)
                )
            ).replace('\n', '\n    ')

    decls_, ops = zip(*body.decls)

    # generate some C code!
    code = dedent('''\
        #include <functional>
        #include <memory>
        #include <string>
        enum type_t {{ {types} }};
        typedef struct {{
          union {{
            long num;
            std::shared_ptr<std::string> str;
            {conttype}
            type_t type;
          }}
        }} schemetype_t;
        main () {{
        {decls}
        {ops}
        return {body}->num;
        }}
        ''').format(
            types=', '.join(TYPES),
            conttype=conttype,
            decls='\n'.join(d for d in decls_ if d),
            ops='\n'.join(ops),
            body=str(body)
            )

    return code

def pretty_C(code, nspace=2):
    unindent = nspace // 2
    # prettify code
    pretty_code = code.splitlines()
    indent = 0
    for i, line in enumerate(pretty_code):
        line = line.strip()
        j = 0
        if len(line) and line[0] == '}':
            indent -= 1
            j = 1
        if ((len(line) > 4 and line[:5].lower() == 'case ') or
            (len(line) > 7 and line[:7].lower() == 'default' and line[7] in (' ', ':'))):
            prefix = ' ' * (nspace * indent - unindent)
        else:
            prefix = ' ' * (nspace * indent)
        pretty_code[i] = prefix + line
        for char in line[j:]:
            if char == '{':
                indent += 1
            elif char == '}':
                indent -= 1
    return '\n'.join(pretty_code)
