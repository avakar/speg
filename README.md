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

To start parsing, construct a `Parser` object and pass the string as an
argument. The string can be an arbitrary object that has a length (i.e. the
`len` function can be called on it) and supports basic slicing. This includes
both unicode strings and bytes objects. It also happens to include rope
objects from the [grope][2] library.

 [2]: https://github.com/avakar/grope

The parser keeps track of how much string has been parsed so far. The index of
the next string element can be queries from the `index` property. The parsing
starts at index 0.

    p = Parser('1 + (2 - 3)')
    assert p.index == 0

The part of the string that lies in front of the `index` is called the *tail* of
the input. You move the parser forward by matching against the beginning of the
tail. When matched, the parser moves forward by the amount matched. This is also
referred to as *consuming the input*.

Use the `eat` method of the parser to match against a literal string.

    p.eat('1 +')

The matching can either succeed, in which case the parser moves forward by the
amount matched, or fail, in which case an exception of type `ParsingFailure` is
raised. 

You move the parser forward by matching against the 

forward by calling `skip` and specifying the number of
elements to jump over. All 

The part of the string that's ahead is called a *tail* and can be retrieved.