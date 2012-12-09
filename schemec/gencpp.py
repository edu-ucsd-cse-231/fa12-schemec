
from collections import OrderedDict
from random import choice
from re import compile as re_compile
from string import hexdigits
from textwrap import dedent

from schemec.typs import (
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
    Token,
    gensym,
    unkpos,
    )

__all__ = [
    'gen_cpp',
    'halt',
    'pretty_cpp'
    ]

NUM, LAM, STR = 'NUM', 'LAM', 'STR'
TYPES = [NUM, LAM, STR]

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
    lams_dict = {}
    # so we can print the original exp if we want
    def find_lams(exp):
        if isinstance(exp, LamExp):
            lams_dict[exp] = exp
        return exp
    rootExp.map(find_lams)
    # all the work
    def find_holes(exp):
        holes = set()
        if isinstance(exp, Halt):
            holes_dict[lams_dict[exp]] = list()
        elif isinstance(exp, VarExp):
            if not is_primop(exp.name):
                holes.add(exp)
        elif isinstance(exp, LamExp):
            holes |= exp.bodyExp
            for arg in exp.argExps:
                holes -= arg
            holes_dict[lams_dict[exp]] = list(holes)
        elif isinstance(exp, AtomicExp):
            pass
        elif isinstance(exp, AppExp):
            holes |= exp.funcExp
            for arg in exp.argExps:
                holes |= arg
        elif isinstance(exp, IfExp):
            holes |= exp.condExp
            holes |= exp.thenExp
            holes |= exp.elseExp
        elif isinstance(exp, LetRecExp):
            holes |= exp.bodyExp
            for var, val in exp.bindings:
                holes |= val
                holes -= var
        elif isinstance(exp, BeginExp):
            unimplemented(exp)
        elif isinstance(exp, SetExp):
            unimplemented(exp)
        elif isinstance(exp, SetThenExp):
            unimplemented(exp)
        else:
            unimplemented(exp)
        return holes
    rootExp.map(find_holes)
    return holes_dict

class CppCode:
    def __init__(self, typ, code, decls):
        self.typ = typ
        self.code = code
        self.decls = decls
    def __str__(self):
        return self.code
    def __repr__(self):
        return self.code
    def map(self, f, skip=True):
        return f(self)
    @property
    def decls_ops(self):
        if len(self.decls):
            decls, ops = zip(*self.decls)
        else:
            decls, ops = [], []
        return (
            '\n'.join(d for d in decls if d),
            '\n'.join(o for o in ops if o)
            )
    def toSExp(self):
        return Token(unkpos, 'cpp')

class LamGenCpp:
    def __init__(self, exp):
        self.holes = compute_holes(exp)
        self._decls = OrderedDict()
        self.nargs = set()
    def __getitem__(self, exp):
        assert isinstance(exp, LamExp)
        if exp.name not in self._decls:
            self.nargs.add(len(exp.argExps))
            holes = self.holes[exp]
            decls, ops = exp.bodyExp.decls_ops
            init_args = ', '.join('schemetype_t {0}'.format(str(hole)) for hole in holes)
            priv = '\n  '.join('schemetype_t {0};'.format(str(var)) for var in holes + exp.argExps)
            destroy_ops = '\n  '.join('{0}.reset();'.format(str(var)) for var in holes + exp.argExps)
            asmts_ = (
                ['{0}({0})'.format(str(hole)) for hole in holes] +
                ['{0}(schemetype_t())'.format(str(arg)) for arg in exp.argExps]
                )
            asmts = ', '.join(asmts_)
            self._decls[exp] = (
                dedent('''\
                    class {cls} : public lambda {{
                     public:
                      {cls}({init_args});
                      ~{cls}();
                      void args({args});
                      schemetype_t operator()();
                     private:
                      {priv}
                    }};''').format(
                        cls=exp.name,
                        init_args=init_args,
                        args=', '.join('schemetype_t' for _ in range(len(exp.argExps))),
                        priv=priv
                        ),
                dedent('''\
                    {cls}::{cls}({init_args}) : {asmts} {{
                      _ready = false;
                    }}
                    {cls}::~{cls}() {{
                      {destroy_ops}
                    }}
                    void {cls}::args({args}) {{
                    #ifdef DEBUG
                      printf("assigning arguments to {cls}\\n");
                    #endif
                      {args_ops}
                      _ready = true;
                    }}
                    schemetype_t {cls}::operator()() {{
                      {decls}
                    #ifdef DEBUG
                      printf("executing {cls}\\n");
                    #endif
                      {ops}
                      {body}
                    }}''').format(
                        cls=exp.name,
                        init_args=init_args,
                        asmts=asmts,
                        destroy_ops=destroy_ops,
                        args=', '.join('schemetype_t _{0}'.format(str(arg)) for arg in exp.argExps),
                        args_ops='\n  '.join('{0} = std::move(_{0});'.format(str(arg)) for arg in exp.argExps),
                        decls=decls,
                        ops=ops,
                        body='return {0};'.format(str(exp.bodyExp))
                        )
                )
        return exp.name
    @property
    def decls_ops(self):
        min_nargs = min(self.nargs)
        max_nargs = max(self.nargs)
        decl = dedent('''\
            class lambda {{
             public:
              {virtuals}
              virtual schemetype_t operator()();
              operator bool() const;
             protected:
              bool _ready;
            }};
            ''').format(
                virtuals='\n  '.join(
                    'virtual void args({0});'.format(
                        ', '.join('schemetype_t' for _ in range(i))
                        )
                    for i in range(min_nargs, max_nargs + 1)
                    )
                )
        op = ''.join(
            dedent('''\
                void lambda::args({0}) {{
                  printf("error: lambda called with an improper number of arguments\\n");
                  exit(-1);
                }}
                ''').format(', '.join('schemetype_t _{0}'.format(j) for j in range(i)))
            for i in range(min_nargs, max_nargs + 1)
            )
        op += dedent('''\
            schemetype_t lambda::operator()() {{
              printf("error: this should be impossible\\n");
              exit(-1);
            }}
            lambda::operator bool() const {{
              return _ready;
            }}
            ''')
        if len(self._decls):
            decls, ops = zip(*self._decls.values())
        else:
            decls, ops = [], []
        return (
            decl + '\n'.join(d for d in decls if d),
            op + '\n'.join(o for o in ops if o)
            )

def declare(var, construct=True):
    return 'schemetype_t {0}{1};'.format(
        var,
        '(new schemetype)' if construct else '')

class Halt(LamExp):
    var = gensym('_halt')
    def toSExp(self):
        tok = Token(unkpos, 'halt')
        return tok
    def map(self, f, skip=True):
        return f(self)

halt = Halt(
    [CppCode(VarExp, Halt.var.name, [])],
    CppCode(
        LamExp,
        'schemetype_t()',
        [(
            'int retval = 0;',
            dedent('''\
                switch({arg}->type) {{
                 case {NUM}:
                  printf("%ld\\n", {arg}->num);
                  break;
                 case {LAM}:
                  printf("you want to return a lambda?! really?!\\n");
                  retval = -1;
                  break;
                 case {STR}:
                  printf("%s\\n", {arg}->str->c_str());
                  break;
                 default:
                  printf("error: but our number value is %ld\\n", {arg}->num);
                  retval = -1;
                }}
                exit(retval);''').format(
                    arg=Halt.var.name,
                    NUM=NUM, LAM=LAM, STR=STR)
            )]
        )
    )

def sanitize(exp, prefix_length=10):
    re_safe = re_compile(r'[^a-zA-Z0-9_]+')

    def rename_(var):
        return VarExp('_{0}__{1}'.format(
            ''.join(choice(hexdigits) for _ in range(prefix_length)),
            re_safe.sub('', var.name)
            ))

    subs = {}
    def sanitize_(exp):
        if isinstance(exp, VarExp) and not is_primop(exp.name):
            return subs[exp.name]
        elif isinstance(exp, LamExp):
            for arg in exp.argExps:
                if isinstance(arg, VarExp):
                    subs[arg.name] = rename_(arg)
        elif isinstance(exp, LetRecExp):
            for var, _ in exp.bindings:
                if isinstance(var, VarExp):
                    subs[var.name] = rename_(var)
        return exp

    return exp.map(sanitize_, skip=False)

def gen_cpp(exp):

    exp = sanitize(exp)

    # compute the holes at each LamExp
    holes = compute_holes(exp)
    lambda_gen = LamGenCpp(exp)

    # map function
    def to_cpp(exp):
        code = None

        decls = []

        if isinstance(exp, VarExp):
            code = exp.name
        elif isinstance(exp, (NumExp, BoolExp, StrExp)):
            if isinstance(exp, NumExp):
                val = str(exp.val)
                sym = '_num'
                typ = NUM
            elif isinstance(exp, BoolExp):
                val = '1' if exp.val else '0'
                sym = '_bool'
                typ = NUM
            elif isinstance(exp, StrExp):
                val = '"{0}"'.format(exp.val)
                sym = '_str'
                typ = STR
            else:
                assert(0)
            tmp = gensym(sym)
            decl = (
                declare(tmp),
                dedent('''\
                    {var}->type = {typ};
                    {var}->{loc} = {val};''').format(
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
            cls = lambda_gen[exp]
            # instantiate a temporary to fill with our lambda
            tmp = gensym('_lam')
            decl = (
                declare(tmp),
                dedent('''\
                    {var}->type = {LAM};
                    {var}->lam = lambda_t(new {cls}({holes}));''').format(
                        var=tmp.name,
                        cls=cls,
                        holes=', '.join(hole.name for hole in holes[exp]),
                        LAM=LAM
                        )
                )
            decls.append(decl)
            code = tmp.name
        elif isinstance(exp, AppExp):
            for arg in exp.argExps:
                decls.extend(arg.decls)
            decls.extend(exp.funcExp.decls)
            tmp = gensym('_ret')
            func = str(exp.funcExp)
            if is_primop(func):
                prim = gensym('_prim')
                typ, body = gen_primop(func, prim, *[str(arg) for arg in exp.argExps[:-1]])
                decl = (
                    declare(prim) + '\nschemetype_t {0};'.format(tmp.name),
                    dedent('''\
                        {prim}->type = {typ};
                        {body}
                        {func}->lam->args({prim});
                        {var} = {func};''').format(
                            prim=prim.name,
                            body=body,
                            typ=typ,
                            var=tmp.name,
                            func=str(exp.argExps[-1]),
                            LAM=LAM
                            )
                    )
                decls.append(decl)
            elif exp.funcExp.typ == VarExp:
                decl = (
                    'schemetype_t {0};'.format(tmp.name),
                    dedent('''\
                        {func}->lam->args({args});
                        {var} = {func};''').format(
                            func=str(exp.funcExp),
                            args=', '.join(str(arg) for arg in exp.argExps),
                            var=tmp.name,
                            LAM=LAM
                            )
                    )
                decls.append(decl)
            else:
                raise RuntimeError('AppExp unimplemented for funcExp of type: {0}'.format(str(exp.funcExp.typ)))
            code = tmp.name
        elif isinstance(exp, IfExp):
            decls.extend(exp.condExp.decls)
            then_decls, then_ops = exp.thenExp.decls_ops
            else_decls, else_ops = exp.elseExp.decls_ops
            tmp = gensym('_ret')
            decl = (
                'schemetype_t {0};'.format(tmp.name),
                dedent('''\
                    if ({cond}->num) {{
                      {then_decls}
                      {then_ops}
                      {var} = std::move({then});
                    }}
                    else {{
                      {else_decls}
                      {else_ops}
                      {var} = std::move({else_});
                    }}''').format(
                        var=tmp.name,
                        cond=str(exp.condExp),
                        then_decls=then_decls,
                        then_ops=then_ops,
                        then=str(exp.thenExp),
                        else_decls=else_decls,
                        else_ops=else_ops,
                        else_=str(exp.elseExp)
                        )
                )
            decls.append(decl)
            code = tmp.name
        elif isinstance(exp, LetRecExp):
            for var, body in exp.bindings:
                decls.extend(body.decls)
                decl = (
                    declare(var),
                    dedent('''\
                        {var}->type = {LAM};
                        {var}->lam = {body}->lam;''').format(
                            var=str(var),
                            body=str(body),
                            LAM=LAM
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
        elif isinstance(exp, CppCode):
            return exp
        else:
            unimplemented(exp)
        return CppCode(type(exp), code, decls)

    body = exp.map(to_cpp)

    main_decls, main_ops = body.decls_ops
    lambda_decls, lambda_ops = lambda_gen.decls_ops

    next = gensym('_next');

    # generate some C code!
    code = dedent('''\
        #include <cstdio>
        #include <cstdlib>
        #include <memory>
        #include <string>
        enum type_t {{ {types} }};
        // forward decls -----------------------------------------------------------------------------------
        class lambda;
        class schemetype;
        typedef std::shared_ptr<lambda> lambda_t;
        typedef std::shared_ptr<schemetype> schemetype_t;
        // lambda decl -------------------------------------------------------------------------------------
        {lambda_decls}
        // schemetype decl ---------------------------------------------------------------------------------
        class schemetype {{
         public:
          union {{
            long num;
            lambda_t lam;
            std::shared_ptr<std::string> str;
          }};
          type_t type;
          schemetype();
          ~schemetype();
        }};
        // lambda impl -------------------------------------------------------------------------------------
        {lambda_ops}
        // schemetype impl ---------------------------------------------------------------------------------
        schemetype::schemetype() {{ }}
        schemetype::~schemetype() {{
          lam.reset();
          str.reset();
        }}
        // main --------------------------------------------------------------------------------------------
        int main() {{
          {next_decl}
          {main_decls}
          {main_ops}
          {next} = {body};
          // next
          while (true) {{
            if (*({next}->lam)) {{
              {next} = std::move((*({next}->lam))());
            }}
            else {{
              printf("error: lambda called before providing arguments!\\n");
              exit(-1);
            }}
          }}
          return 0;
        }}
        ''').format(
            types=', '.join(TYPES),
            lambda_decls=lambda_decls,
            lambda_ops=lambda_ops,
            next_decl=declare(next, False),
            next=next,
            main_decls=main_decls,
            main_ops=main_ops,
            body=str(body)
            )

    return code

def pretty_cpp(code, nspace=2):
    TERMINATORS = (' ', '\t', ':')
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
        if len(line) and line[0] == '#':
            prefix = ''
        elif ((len(line) >= 5 and line[:5].lower() == 'case ') or
            (len(line) >= 6 and line[:6].lower() == 'public'  and line[6] in TERMINATORS) or
            (len(line) >= 7 and line[:7].lower() == 'default' and line[7] in TERMINATORS) or
            (len(line) >= 7 and line[:7].lower() == 'private' and line[7] in TERMINATORS)):
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
