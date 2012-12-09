
from functools import partial
from textwrap import dedent

from schemec.cps import T_c
from schemec.typs import (
    AppExp,
    VarExp,
    AtomicExp,
    LamExp,
    NumExp,
    StrExp,
    BoolExp,
    IfExp,
    LetRecExp,
    gensym
    )

class CodeGenerator():
    """ The code generator
    """
    def __init__(self):
        self.lambdaBindings = {}
        self.rv = VarExp('returnValue')
        self.rvtype = 0
        self.ivars = set()
        self.svars = set()
        self.fvars = set()
        self.ibprimitives = {
            '+': '+',
            '-': '-',
            '*': '*',
            '=': '=='
            }
        self.ibprimFormat = '{0}->_num = {1}->_num {op} {2}->_num;\n'
        self.iuprimitives = {
            'zero?': '== 0'
            }
        self.iuprimFormat = '{0}->_num = {1}->_num {op};\n'
        self.tmpvar = gensym('_')
        self.sprimitives = {
            'string-append': '{0}->_str.append({1}->_str);',
            'string=?': '{0}->_num = 1 - abs(strcmp({1}->_str, {2}->_str));\n'
            }
        self.sprimrts = {
            'string-append': self.setStrVar,
            'string=?': self.setIntVar
            }
        self.primops = (
            self.ibprimitives.keys() |
            self.iuprimitives.keys() |
            self.sprimitives.keys()
            )
        self.retExp = LamExp([self.rv], self.rv)
        self.declareCode = ''
        self.argVars = [VarExp('_args[{0}]'.format(i)) for i in range(10)]
        self.ivars.update(self.argVars)
        self.lam_holes = {}

    """
    Translates the given CPS expression into C
    @type exp: a CPS expression
    @param exp: the expression to translate
    """
    def code_gen(self, exp):
        self.lam_holes = self.compute_holes(exp)
        maxvars = max(len(lam.argExps) for lam in self.lam_holes.keys())
        body = self.toC(exp, self.rv, indent=1)
        return dedent('''\
            #include <functional>
            #include <memory>
            #include <string>
            enum type_t {{ BOOL, NUM, STR, CONT }};
            typedef struct {{
              union {{
                bool _bool;
                long _num;
                std::shared_ptr<std::string> _str;
                union {{
                  {conttypes}
                }} _cont;
              }}
              type_t type;
            }} schemetype_t;
            main () {{
            {declarations}
            {body}
            }}
            ''').format(
                conttypes='\n    '.join(
                    'std::function<std::unique_ptr<schemetype_t*>({0})> _{1};'.format(
                        ', '.join('std::unique_ptr<schemetype_t*>' for _ in range(i)),
                        i) for i in range(maxvars)
                    ),
                declarations=self.declareCode,
                body=body
                )

    def compute_holes(self, rootExp):
        holes_dict = {}
        def find_holes(holes, exp):
            if isinstance(exp, LamExp):
                holes_dict[exp] = holes - set(exp.argExps)
                holes -= set(exp.argExps)
            elif isinstance(exp, VarExp):
                if exp.name not in self.primops:
                    holes.add(exp)
            return exp
        rootExp.map(partial(find_holes, set()))
        return holes_dict

    """
    Translates the given CPS expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: a CPS expression
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def toC(self, exp, assignTo, indent=0):
        if isinstance(exp, IfExp):
            return self.ifToC(exp, assignTo, indent)
        elif isinstance(exp, AppExp):
            return self.appToC(exp, assignTo, indent)
        elif isinstance(exp, LamExp):
            return self.lamToC(exp, assignTo, indent)
        elif isinstance(exp, AtomicExp):
            return self.atmToC(exp, assignTo, indent)
        elif isinstance(exp, LetRecExp):
            return self.letrecToC(exp, assignTo, indent)
        else:
            raise RuntimeError('unimplemented expression type: {0}'.format(str(type(exp))))

    """
    Translates the given atomic expression into C such that the result of the
    computation will be assigned to the specified variable. Careful: do not use
    with lambda expressions!

    @type exp: an AtomicExp (except LamExp)
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def atmToC(self, exp, assignTo=None, indent=0):
        if assignTo is None:
            code = '  ' * indent
            if isinstance(exp, BoolExp):
                code += 'true' if exp.val else 'false'
            elif isinstance(exp, NumExp):
                code += str(exp.val)
            elif isinstance(exp, VarExp):
                code += exp.name
            elif isinstance(exp, StrExp):
                tmp = gensym('_')
                self.declareVar(tmp, val)
                code += tmp.name
            else:
                raise RuntimeError('unhandled AtomicExp in atmToC()')
            return code
        else:
            self.declareVar(assignTo)
            if isinstance(exp, VarExp):
                return '  ' * indent + '{0} = {1};\n'.format(assignTo.name, exp.name)
                #~ return dedent('''\
                    #~ {0}.intVal = {1}.intVal;
                    #~ strcpy({0}.strVal, {1}.strVal);
                    #~ {0}.label = {1}.label;
                #~ ''').format(assignTo.name, exp.name)
            elif isinstance(exp, StrExp):
                #~ self.setStrVar(assignTo)
                return self.setStr(assignTo, exp, indent)
            else:
                #~ self.setIntVar(assignTo)
                #~ if assignTo in self.svars:
                    #~ self.svars.remove(assignTo)
                return self.setInt(assignTo, exp, indent)

    def isStrVar(self, exp):
        return isinstance(exp, VarExp) and exp in self.svars

    """
    Assign a value (int, bool, int variable) to an integer variable.

    @type var: a VarExp
    @param var: the variable
    @type val: an AtomicExp
    @param val: the value to assign
    """
    def setInt(self, var, val, indent):
        if var is self.rv:
            self.rvtype = 0
        if isinstance(val, VarExp):
            return '  ' * indent + '{0}._num = {1}._num;\n'.format(
                var.name,
                val.name
                )
        elif isinstance(val, NumExp):
            return '  ' * indent + '{0}._num = {1};\n'.format(
                var.name,
                val.val
                )
        else:
            raise RuntimeError('setInt() on something that is not an NumExp')

    """
    Assign a value (string, string variable) to a string variable.

    @type var: a VarExp
    @param var: the variable
    @type val: an AtomicExp
    @param val: the value to assign
    """
    def setStr(self, var, val, indent=0):
        #~ self.setStrVar(var)
        if var is self.rv:
            self.rvtype = 1
        if isinstance(val, VarExp):
            '  ' * indent + '{0}._str = {1}._str;\n'.format(
                var.name,
                val.name
                )
        elif isinstance(val, StrExp):
            '  ' * indent + '{0}._str = std::make_shared<std::string>({1});\n'.format(
                var.name,
                val.val
                )
        else:
            raise RuntimeError('setStr() on something that is not a StrExp')

    """
    Translates the body of a given lambda expression into C such
    that the result of the computation will be assigned to the specified
    variable.

    @type exp: a LamExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def lamToC(self, exp, assignTo, indent=0):
        holes = ', '.join(hole.name + '&' for hole in self.lam_holes[exp])
        args = ', '.join('std::unique_ptr<schemetype_t*> {0}'.format(arg.name) for arg in exp.argExps)
        body = self.toC(exp.bodyExp, assignTo, indent=indent + 2)
        if assignTo is None:
            return dedent('''\
                [{holes}]({args}) -> schemetype& {{
                {body}
                }}''').format(
                    holes=holes,
                    args=args,
                    body=body
                    ).replace('\n', '\n' + '  ' * (indent + 1))
        else:
            code = '  ' * indent + dedent('''\
                std::unique_ptr<schemetype_t*> {var} (new schemetype_t);
                {var}->_cont._{narg} = [{holes}]({args}) -> std::unique_ptr<schemetype_t*> {{
                {body}
                }};
                ''').format(
                    var=assignTo.name,
                    narg=len(exp.argExps),
                    holes=holes,
                    args=args,
                    body=body
                    ).replace('\n', '\n' + '  ' * indent)
            return code

    def printReturn(self, indent=0):
        #~ if self.rvtype is 0:
            #~ formStr = '%i'
            #~ typeStr = 'intVal'
        #~ else:
            #~ formStr = '%s'
            #~ typeStr = 'strVal'
        #~ return ('printf(\"' + formStr + '\\n\", {0}.' + typeStr + ');\nreturn 0;\n').format(self.rv)
        return dedent('''\
            printf(\"integer return value: \\t%i\\n\", {0}._num);
            return 0;
            ''').format(self.rv).replace('\n', '\n' + '  ' * indent)

    """
    Translates the given application expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: an AppExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def appToC(self, exp, assignTo, indent=0):
        if self.isPrimitive(exp.funcExp):
            return self.primToC(exp, assignTo, indent)
        elif isinstance(exp.funcExp, (LamExp, VarExp)):
            if isinstance(exp.funcExp, LamExp) and exp.funcExp.bodyExp == self.rv:
                return self.printReturn(indent)
            else:
                if assignTo is not None:
                    dvar = assignTo.name + ' = '
                else:
                    dvar = ''
                return '  ' * indent + '{dvar}{lvar}._cont._{narg}({args});\n'.format(
                    dvar=dvar,
                    lvar=exp.funcExp.name,
                    narg=len(exp.argExps),
                    args=', '.join(self.toC(arg, None) for arg in exp.argExps)
                    ).replace('\n', '\n' + '  ' * indent)
        else:
            raise RuntimeError('this should not happen. trying to apply {0} of type {1}'.format(exp, type(exp)))

    def letrecToC(self, exp, assignTo, indent=0):
        code = self.argsToC(exp.bindings, indent)
        code += self.toC(exp.bodyExp, assignTo, indent)
        return code

    def isPrimitive(self, funcExp):
        return self.isIBPrimitive(funcExp) or self.isIUPrimitive(funcExp) or self.isSPrimitive(funcExp)

    def isIBPrimitive(self, funcExp):
        return isinstance(funcExp, VarExp) and funcExp.name in self.ibprimitives.keys()

    def isIUPrimitive(self, funcExp):
        return isinstance(funcExp, VarExp) and funcExp.name in self.iuprimitives.keys()

    def isSPrimitive(self, funcExp):
        return isinstance(funcExp, VarExp) and funcExp.name in self.sprimitives.keys()

    """
    Translates the given primitive application into C. The result is passed to the continuation.

    @type exp: an AppExp
    @param exp: the primitive application to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result of the continuation to
    """
    def primToC(self, exp, assignTo, indent=0):
        if self.isIBPrimitive(exp.funcExp):
            setvar = self.setIntVar
            primFormat = self.ibprimFormat.format('{0}', '{1}', '{2}', op=self.ibprimitives[exp.funcExp.name])
            nary = 2
        elif self.isIUPrimitive(exp.funcExp):
            setvar = self.setIntVar
            primFormat = self.iuprimFormat.format('{0}', '{1}', op=self.iuprimitives[exp.funcExp.name])
            nary = 1
        else:
            setvar = self.sprimrts[exp.funcExp.name]
            primFormat = self.sprimitives[exp.funcExp.name]
            nary = 2

        tmp = gensym('_')
        setvar(tmp)
        code = '  ' * indent + dedent('''\
            std::unique_ptr<schemetype_t*> {0} (new schemetype_t);
            {1}
            ''').format(
                tmp.name,
                primFormat.format(tmp.name, *[self.toC(arg, None) for arg in exp.argExps])
                ).replace('\n', '\n' + '  ' * indent)
        cont = AppExp(exp.argExps[-1], tmp)
        return code + self.toC(cont, assignTo, indent)

    """
    Set a variable to int.

    @type var: a VarExp
    @param var: the variable to set
    """
    def setIntVar(self, var):
        self.ivars.add(var)
        self.svars -= set([var])

    """
    Set a variable to string.

    @type var: a VarExp
    @param var: the variable to set
    """
    def setStrVar(self, var):
        self.svars.add(var)
        self.ivars -= set([var])

    """
    For each tuple in the list translate the argument and assign to respective variable.

    @type args: a list of pairs with a VarExp and an expressions each
    @param vars: the arguments to translate
    """
    def argsToC(self, args, indent=0):
        return ''.join(self.toC(arg, var, indent=indent) for var, arg in args)


    """
    Declare a variable if it hasn't been declared yet

    @type var: a VarExp
    @param var: the variable to declare
    """
    def declareVar(self, var, val=None):
        if val is None:
            self.declareCode += '  schemetype_t {0};\n'.format(var.name) if var not in self.ivars | self.svars else ''
            self.ivars.add(var)
        else:
            if isinstance(val, VarExp):
                suffix = ''
                val = val.name
            elif isinstance(val, NumExp):
                suffix = '._num'
                val = str(val.val)
            elif isinstance(val, BoolExp):
                suffix = '._bool'
                val = 'true' if val.val else 'false'
            elif isinstance(val, StrExp):
                suffix = '._str'
                val = val.val
            else:
                raise RuntimeError('unhandled AtomicExp in declareVar()')
            self.declareCode += '  schemetype_t {0}{1} = {2};\n'.format(
                var.name,
                suffix,
                val
                )

    """
    Translates the given if expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: an IfExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def ifToC(self, exp, assignTo, indent=0):
        if assignTo is not None:
            code = '  ' * indent + 'schemetype_t {0};\n'.format(assignTo.name)
        else:
            code = ''
        return (code + dedent('''\
            if ({cond}{suffix}) {{
              {then}
            }}
            else {{
              {else_}
            }}
            ''').format(
                cond=self.toC(exp.condExp, None),
                suffix='._num' if isinstance(exp.condExp, VarExp) else '',
                then=self.toC(exp.thenExp, assignTo),
                else_=self.toC(exp.elseExp, assignTo)
                )).replace('\n', '\n' + '  ' * indent)

################################################################################
## Main
################################################################################

if __name__ == '__main__':
    #~ exp = AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')),
                 #~ BoolExp(True),
                 #~ BoolExp(False))

    exp = IfExp(IfExp(BoolExp(True), BoolExp(False), BoolExp(True)), StrExp("bla"), StrExp("blubb"))
    #~ exp = AppExp(VarExp('+'), NumExp(1), NumExp(2))
    #~ exp = AppExp(VarExp('string-append'), StrExp("bla"), StrExp("blubb"))
    #~ exp = AppExp(VarExp('+'), AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')), NumExp(3), NumExp(4)), NumExp(2))

    gen = CodeGenerator()
    cpsexp = T_c(exp, gen.retExp)
    #~ print(exp)
    #~ print(cpsexp)
    print(gen.code_gen(cpsexp))
