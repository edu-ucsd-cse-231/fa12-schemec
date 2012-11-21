from textwrap import dedent

from schemec.ast import ast
from schemec.sexp import parse, pretty
from schemec.cps import T_c, halt

if __name__ == '__main__':
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
    print('; original')
    print(evenodd)
    print('; parsed')
    print(pretty(parse(evenodd)))
    print('; ast')
    print(ast(evenodd))
    print('; cps ast')
    print(T_c(ast(evenodd), halt))
