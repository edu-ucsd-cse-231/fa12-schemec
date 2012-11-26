from textwrap import dedent

from schemec.cps import T_c
from schemec.types import *

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
        self.iprimitives = {
            '+': '+',
            '-': '-',
            '*': '*',
            '=': '=='
            }
        self.iprimFormat = '{0}.intVal = {1}.intVal {op} {2}.intVal;\n'
        self.tmpvar = gensym('_')
        self.sprimitives = {
            'string-append': dedent('''\
                    strcat({0}.strVal, {1}.strVal);
                    strcat({0}.strVal, {2}.strVal);'''),
            'string=?': '{0}.intVal = 1 - abs(strcmp({1}.strVal,{2}.strVal));\n'
            }
        self.sprimrts = {
            'string-append': self.setStrVar,
            'string=?': self.setIntVar
            }
        self.retExp = LamExp([self.rv], self.rv)
        self.declareCode = ''

    """
    Translates the given CPS expression into C
    @type exp: a CPS expression
    @param exp: the expression to translate
    """
    def code_gen(self, exp):
        preamble = dedent('''\
            #include<stdio.h>
            #include<string.h>
            #define True 1
            #define False 0
            typedef struct {
              int intVal;
              char strVal[256];
              void * label;
            } schemetype;
            main()
            {
            ''')
        
        code = self.toC(exp, self.rv)
        return preamble + self.declareCode + code + "\n}\n"

    """
    Translates the given CPS expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: a CPS expression
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def toC(self, exp, assignTo):
        if (isinstance(exp, IfExp)):
            return self.ifToC(exp, assignTo)
        if (isinstance(exp, AppExp)):
            return self.appToC(exp, assignTo)
        if (isinstance(exp, LamExp)):
            return self.lamToC(exp, assignTo)
        if (isinstance(exp, AtomicExp)):
            return self.atmToC(exp, assignTo)
        if (isinstance(exp, LetRecExp)):
            return self.letrecToC(exp, assignTo)
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
    def atmToC(self, exp, assignTo):
        val = exp.val if isinstance(exp, BoolExp) else exp
        if assignTo is None:
            return str(val)
        else:
            self.declareVar(assignTo)
            if isinstance(exp, StrExp) or self.isStrVar(exp):
                self.setStrVar(assignTo)
                return self.setStr(assignTo, val)
            else:
                self.setIntVar(assignTo)
                if assignTo in self.svars:
                    self.svars.remove(assignTo)
                return self.setInt(assignTo, val)

    def isStrVar(self, exp):
        return isinstance(exp, VarExp) and exp in self.svars

    """
    Assign a value (int, bool, int variable) to an integer variable.

    @type var: a VarExp
    @param var: the variable
    @type val: an AtomicExp
    @param val: the value to assign
    """
    def setInt(self, var, val):
        if var is self.rv:
            self.rvtype = 0
        end = '.intVal' if isinstance(val, VarExp) else ''
        return ('{0}.intVal = {1}' + end + ';\n').format(var, val)

    """
    Assign a value (string, string variable) to a string variable.

    @type var: a VarExp
    @param var: the variable
    @type val: an AtomicExp
    @param val: the value to assign
    """
    def setStr(self, var, val):
        if var is self.rv:
            self.rvtype = 1
        end = '.strVal' if isinstance(val, VarExp) else ''
        return ('strcpy({0}.strVal,{1}' + end + ');\n').format(var, val)

    """
    Translates the body of a given lambda expression into C such
    that the result of the computation will be assigned to the specified
    variable.

    @type exp: a LamExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def lamToC(self, exp, assignTo):
        label = gensym('lrb_').name
        code = '{0}.label = &&{1};\n'.format(assignTo.name, label)
        
        sym = gensym('lr_').name
        code = 'goto {0};\n'.format(sym)
        
        #~ self.lambdaBindings[assignTo] = (label, exp.vars)
        code += dedent('''\
                {0}:
                {1}
                ''').format(label, self.toC(exp.bodyExp, self.tmpvar))
        code += '{0}:\n'.format(sym)
        return code

    """
    Translates the given application expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: an AppExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def appToC(self, exp, assignTo):
        if self.isPrimitive(exp.funcExp):
            return self.primToC(exp, assignTo)
        elif isinstance(exp.funcExp, VarExp):
            # TODO: pass vars in an array
            return self.argsToC(zip(vars, exp.argExps)) + dedent('''\
                    goto * {0}.label;
                    ''').format(VarExp.name)
            #~ funcExp = self.lambdaBindings[exp.funcExp]
        elif isinstance(exp.funcExp, LamExp):
            code = self.argsToC(zip(exp.funcExp.vars, exp.argExps))
            if exp.funcExp.bodyExp == self.rv:
                if self.rvtype is 0:
                    formStr = '%i'
                    typeStr = 'intVal'
                else:
                    formStr = '%s'
                    typeStr = 'strVal'
                return code + ('printf(\"' + formStr + '\\n\", {0}.' + typeStr + ');\nreturn 0;\n').format(self.rv)
            else:
                return code + self.toC(exp.funcExp.bodyExp, assignTo)
        else:
            raise RuntimeError('this should not happen. trying to apply {0} of type {1}'.format(exp, type(exp)))

    def letrecToC(self, exp, assignTo):
        code = self.argsToC(exp.bindings)
        code += self.toC(exp.bodyExp, assignTo)
        return code

    def isPrimitive(self, funcExp):
        return self.isIPrimitive(funcExp) or self.isSPrimitive(funcExp)

    def isIPrimitive(self, funcExp):
        return isinstance(funcExp, VarExp) and funcExp.name in self.iprimitives.keys()

    def isSPrimitive(self, funcExp):
        return isinstance(funcExp, VarExp) and funcExp.name in self.sprimitives.keys()

    """
    Translates the given primitive application into C. The result is passed to the continuation.

    @type exp: an AppExp
    @param exp: the primitive application to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result of the continuation to
    """
    def primToC(self, exp, assignTo):
        if self.isIPrimitive(exp.funcExp):
            setvar = self.setIntVar
            primFormat = self.iprimFormat.format('{0}','{1}','{2}',op=self.iprimitives[exp.funcExp.name])
        else:
            setvar = self.sprimrts[exp.funcExp.name]
            primFormat = self.sprimitives[exp.funcExp.name]

        a, b, c = [gensym('_') for i in range(3)]
        code = self.argsToC(zip([a,b], exp.argExps[:-1]))
        self.declareVar(c)
        setvar(c)
        code += primFormat.format(c.name, a.name, b.name)
        cont = AppExp(exp.argExps[-1],c)
        return code + self.toC(cont, assignTo)

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
    def argsToC(self, args):
        code = ''
        for (var,arg) in args:
            code += self.toC(arg, var)
        return code
        

    """
    Declare a variable if it hasn't been declared yet

    @type var: a VarExp
    @param var: the variable to declare
    """
    def declareVar(self, var):
        self.declareCode += 'schemetype {0};\n'.format(var) if var not in self.ivars | self.svars else ''
        self.ivars.add(var)

    """
    Translates the given if expression into C such that the result of the
    computation will be assigned to the specified variable.

    @type exp: an IfExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def ifToC(self, exp, assignTo):
        self.declareVar(assignTo)
        code = 'if ({0})\n{{{1}}}\nelse\n{{{2}}}\n'.format(self.toC(exp.condExp, None),
                                                            self.toC(exp.thenExp, assignTo),
                                                            self.toC(exp.elseExp, assignTo))
        return code

################################################################################
## Main
################################################################################

if __name__ == '__main__':
    #~ exp = AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')),
                 #~ BoolExp(True),
                 #~ BoolExp(False))

    #~ exp = IfExp(IfExp(BoolExp(True), BoolExp(False), BoolExp(True)), StrExp("bla"), StrExp("blubb"))
    #~ exp = AppExp(VarExp('+'), NumExp(1), NumExp(2))
    exp = AppExp(VarExp('string-append'), StrExp("bla"), StrExp("blubb"))
    #~ exp = AppExp(VarExp('+'), AppExp(LamExp([VarExp('g'), VarExp('h')], VarExp('g')), NumExp(3), NumExp(4)), NumExp(2))

    gen = CodeGenerator()
    cpsexp = T_c(exp, gen.retExp)
    #~ print(exp)
    #~ print(cpsexp)
    print(gen.code_gen(cpsexp))
