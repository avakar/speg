# speg

[![Build Status](https://travis-ci.org/avakar/speg.svg?branch=master)](https://travis-ci.org/avakar/speg)

A library for writing recursive descent parsers in Python.

## Getting started

Install from [PyPI][1].

    pip install speg

Write your parser.

    from speg import parse

    def _digit(p):
        s = p.re(r'[0-9]+')
        return int(s, 10)

    def _operator(p):
        with p:
            p.eat('+')
            return lambda a, b: a + b

        p.eat('-')
        return lambda a, b: a - b

    def _atom(p):
        with p:
            p.eat('(')
            r = p(_expression)
            p.eat(')')
            return r
        return p(_digit)

    def _expression(p):
        lhs = p(_atom)
        while p:
            with p:
                op = p(_operator)
                rhs = p(_atom)
                lhs = op(lhs, rhs)

        return lhs

    def evaluate_expr(text):
        return parse(text, _expression)

And use it.

    >>> evaluate_expr('2+2')
    4

    >>> evaluate_expr('2-(1+1)')
    0

Enjoy excellent error reporting.

    >>> evaluate_expr('2-(1+1')
    speg.errors.ParseError: at 1:7: expected ')' or <operator>

    >>> evaluate_expr('2*2')
    speg.errors.ParseError: at 1:2: expected <operator> or end of input

    >>> evaluate_expr('2+(-2)')
    speg.errors.ParseError: at 1:4: expected <expression>

 [1]: https://pypi.org/project/speg/

## Documentation

