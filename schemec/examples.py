
from textwrap import dedent

from ast import ast
from sexp import parse, pretty
from cps import T_c, halt

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
      (even? 88))
    ''')
    print(pretty(parse(evenodd)))
    print(ast(evenodd))
    print(T_c(ast(evenodd), halt))
