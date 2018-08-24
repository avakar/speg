# speg

[![Build Status](https://travis-ci.org/avakar/speg.svg?branch=master)](https://travis-ci.org/avakar/speg)

A PEG-based parser interpreter with memoization.

## Installation

The parser is tested on Python 2.7 and 3.4.

    pip install speg

    with parse(text) as p:
        p('text')
        num, _ = p.re(r'[0-9]+')
        p.eof()

    with p:
        p(_ws)

    # equivalent to `with p.opt:`
    with p:
        with p:
            p(x)

    with p:
        p(x)
    if p:
        p.fail()
