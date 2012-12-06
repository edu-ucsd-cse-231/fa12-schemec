from textwrap import dedent

from schemec.ast import ast
from schemec.sexp import parse, pretty
from schemec.cps import T_c, halt
from schemec.code_gen import CodeGenerator

def main():
    fac5 = dedent('''\
    ;; factorial : number -> number
    ;; to calculate the product of all positive
    ;; integers less than or equal to n.
    (letrec ((fact
      (lambda (x)
        (if (= x 0)
          1
          (* x (fact (- x 1)))))))
      (fact 5))
    ''')
    evenodd = dedent('''\
    (letrec ((even?
              (lambda (n)
                (if (zero? n)
                    #t
                    (odd? (- n 1)))))
             (odd?
              (lambda (n)
                (if (zero? n)
                    #f
                    (even? (- n 1))))))
      (even? 88))''')
    e = fac5
    print('; original')
    print(e)
    print('; parsed')
    e_parsed = parse(e)
    print(pretty(e_parsed))
    print('; ast')
    e_ast = ast(e)
    print(e_ast)
    print('; cps ast')
    e_cps = T_c(e_ast, halt)
    print(e_cps)
    print('; C code')
    gen = CodeGenerator()
    e_cps = T_c(e_ast, gen.retExp)
    print('; cps ast for codegen')
    print(e_cps)
    print(gen.code_gen(e_cps))
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
