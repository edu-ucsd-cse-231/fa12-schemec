from textwrap import dedent

from schemec.ast import ast
from schemec.sexp import parse, pretty
from schemec.cps import T_c
from schemec.gencpp import halt, gen_cpp, pretty_cpp
from schemec.opt import optimize

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
      (fact 12))
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
      (even? 87))''')
    e = fac5 # evenodd
#     print('; original')
#     print(e)
#     print('; parsed')
#     e_parsed = parse(e)
#     print(pretty(e_parsed))
#     print('; ast')
    e_ast = ast(e)
#     print(e_ast)
#     print('; cps ast')
    e_cps = optimize(T_c(e_ast, halt))
#     print(e_cps)
#     print('; C code')
#     print('; cps ast for codegen')
    print(pretty_cpp(gen_cpp(e_cps), 4))
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
