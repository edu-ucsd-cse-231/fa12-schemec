from types import *    

class CodeGenerator():
    """ The code generator
    """
    def __init__(self):
        self.lambdaBindings = {}
        self.rv = VarExp('returnValue')
        self.vars = set([self.rv])
        self.gensym = GenSym()
    
    """
    Translates the given CPS expression into C
    @type exp: a CPS expression
    @param exp: the expression to translate
    """
    def code_gen(self, exp):
        code = ('#include<stdio.h>\n'
                '#define True 1\n'
                '#define False 0\n'
                '\n'
                'main()\n'
                '{\n'
                'int returnValue;\n')
        code += self.toC(exp, self.rv)
        return code + "\n}\n"

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
        code = ''
        end = ''
        if not assignTo is None:
            code = self.declareVar(assignTo)
            code += '{0} = '.format(assignTo)
            end = ';\n'
        val = exp.val if isinstance(exp, BoolExp) else exp
        return code + '{0}'.format( val) + end
    
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
        if exp.bodyExp == self.rv:
            return "printf(\"%i\\n\", {0});\nreturn 0;\n".format(self.rv)
        return self.toC(exp.bodyExp, assignTo)
    
    """
    Translates the given application expression into C such that the result of the 
    computation will be assigned to the specified variable. 
    
    @type exp: an AppExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def appToC(self, exp, assignTo):
        funcExp = self.lambdaBindings[exp.funcExp] if isinstance(exp.funcExp, VarExp) else exp.funcExp
        return ''.join([self.argsToC(funcExp.vars, exp.argExps), self.toC(funcExp, assignTo)])
    
    """
    Translates a list of arguments to C and assigns the results to respectiv variables.
    
    @type vars: a list of VarExp
    @param vars: the variables to assign the arguments to
    @type argExps: a list of expressions
    @param vars: the arguments to translate
    """
    def argsToC(self, vars, argExps):
        code = ''
        for (var,arg) in zip(vars, argExps):
            if (isinstance(arg, LamExp)):
                self.lambdaBindings[var] = arg
            else:
                code += self.toC(arg, var)
        return code

    """
    Declare a variable if it hasn't been declared yet
    
    @type var: a VarExp
    @param var: the variable to declare
    """
    def declareVar(self, var):
        return 'int {0};\n'.format(var) if var not in self.vars else ''

    """
    Translates the given if expression into C such that the result of the 
    computation will be assigned to the specified variable. 
    
    @type exp: an IfExp
    @param exp: the expression to translate
    @type assignTo: a VarExp
    @param exp: the variable to assign the result to
    """
    def ifToC(self, exp, assignTo):
        code = self.declareVar(assignTo)
        code += 'if ({0})\n{{{1}}}\nelse\n{{{2}}}\n'.format(self.toC(exp.condExp, None), 
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
                 
    exp = IfExp(IfExp(BoolExp(True), BoolExp(False), BoolExp(True)), NumExp(1), NumExp(0))
    
    gen = CodeGenerator()
    cpsexp = T_c(exp, LamExp([gen.rv],gen.rv))

    print(gen.code_gen(cpsexp))
