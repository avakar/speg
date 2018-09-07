from speg import parse, ParseError, re, hidden
import pytest

def test_simple():
    assert parse('', lambda p: p.eat('')) == ''
    assert parse('test', lambda p: p.eat('')) == ''
    assert parse('test', lambda p: p.eat('t')) == 't'
    assert parse('test', lambda p: p.eat('te')) == 'te'

def test_re():
    @re(r'..')
    def double(s): return s

    def rule(p):
        return p.parse(double), p.parse(double)

    assert parse('test', rule) == ('te', 'st')

def test_vars():
    def nested(p):
        assert 'v' in p.vars
        assert p.vars['v'] == 1

        p.vars['v'] = 2
        assert p.vars['v'] == 2

        assert 'w' not in p.vars
        p.vars['w'] = 3
        assert 'w' in p.vars
        assert p.vars['w'] == 3

    def root(p):
        assert 'v' not in p.vars
        assert not ('v' in p.vars)

        assert p.vars.get('v') is None
        assert p.vars.get('v', None) is None
        assert p.vars.get('v', 'x') == 'x'
        assert p.vars.get('v', 1) == 1

        with pytest.raises(KeyError):
            p.vars['v']

        p.vars['v'] = 1

        assert 'v' in p.vars
        assert p.vars.get('v') == 1
        assert p.vars.get('v', None) == 1
        assert p.vars['v'] == 1

        p.parse(nested)

        assert p.vars['v'] == 1
        assert 'w' not in p.vars

    parse('', root)

# def test_re():
#     with parser("3141569") as p:
#         n = p.re(r'[123]*')
#         assert n == '31'
#         assert p.index == 2

def test_simple_fail():
    with pytest.raises(ParseError):
        parse('', lambda p: p.eat('t'))

# def test_simple_rule():
#     def root(p):
#         return 2 * p.re('.')
#     with parser("test") as p:
#         assert p(root) == 'tt'

def test_eof():
    def _empty_lang(p):
        p.check_eof()
    parse('', _empty_lang)

def test_failed_eof():
    def _empty_lang(p):
        p.check_eof()
    try:
        parse('xx', _empty_lang)
        assert False
    except ParseError as e:
        assert str(e) == 'at 1:1: expected <empty lang>'
        # assert e.start_pos.index == 0
        # assert e.end_pos.index == 0

    def _x_lang(p):
        p.eat('x')
        p.check_eof()
    try:
        parse('xx', _x_lang)
        assert False
    except ParseError as e:
        assert str(e) == 'at 1:2: expected end of input'
        # assert e.start_pos.index == 1
        # assert e.end_pos.index == 1

def test_sema_error():
    def root(p):
        p.eat('te')
        p.fail()

    with pytest.raises(ParseError):
        parse("test", root)

def test_not():
    @re('[0-9]')
    def digit(s): return s

    @re('[0-9]+')
    def digits(s): return s

    @re('[_a-zA-Z0-9]+')
    def ident_chars(s): return s

    def ident(p):
        p.not_(digit)
        return p.parse(ident_chars)

    def num(p):
        r = p.parse(digits)
        p.not_(ident)
        return int(r, 10)

    assert parse('123', num) == 123

    try:
        parse('123a', num)
        assert False
    except ParseError as e:
        assert str(e) == 'at 1:4: unexpected <ident>'

def test_error_priority():
    def root(p):
        with p:
            return p.parse(num_suffix)
        return p.parse(undef)

    @re(r'[0-9]+')
    def num(r):
        return int(r, 10)

    def num_suffix(p):
        r = p.parse(num)
        p.eat('s')
        return r

    def undef(p):
        p.eat('x')

    try:
        parse("t", root)
        assert False
    except ParseError as e:
        #assert e.start_pos.index == 0
        pass

    try:
        parse("1", root)
        assert False
    except ParseError as e:
        #assert e.start_pos.index == 1
        pass

def test_repr():
    def root(p):
        assert repr(p) == "<speg.Parser at '*test'>"
        p.eat('te')
        assert repr(p) == "<speg.Parser at 'te*st'>"

    parse('test', root)

def test_multiple_exp_fails():
    @re(r'[+\-]')
    def operator(s): return s

    @re(r'[0-9]+')
    def num(s): return int(s, 10)

    def atom_expr(p):
        with p:
            p.eat('(')
            r = p.parse(bin_expr)
            p.eat(')')
            return r
        return p.parse(num)

    def bin_expr(p):
        r = p.parse(atom_expr)

        while p:
            with p:
                op = p.parse(operator)
                rhs = p.parse(atom_expr)

                if op == '+':
                    r += rhs
                elif op == '-':
                    r -= rhs

        return r

    def root(p):
        r = p.parse(bin_expr)
        p.check_eof()
        return r

    assert parse('1', root) == 1
    assert parse('1+1', root) == 2
    assert parse('1+(2+3)', root) == 6
    assert parse('1+(2-3)', root) == 0
    assert parse('1-(2+3)', root) == -4
    assert parse('1-2+3', root) == 2

    try:
        parse('1+', root)
        assert False
    except ParseError as e:
        assert str(e) == 'at 1:3: expected <atom expr>'

def test_hidden_rule():
    def x(p):
        p.eat('x')

    @hidden
    def root(p):
        p.parse(x)
        p.check_eof()

    try:
        parse('y', root)
    except ParseError as e:
        assert str(e) == 'at 1:1: expected <x>'

def test_named_rule():
    def x(p):
        """whizzing frobulator"""
        p.eat('x')

    @hidden
    def root(p):
        p.parse(x)
        p.check_eof()

    try:
        parse('y', root)
    except ParseError as e:
        assert str(e) == 'at 1:1: expected whizzing frobulator'

def test_opt():
    @re(r' +')
    def ws(s):
        return s

    def x(p):
        p.eat('x')

    @hidden
    def root(p):
        p.opt.parse(ws)
        p.parse(x)

    parse('  x', root)
    parse('x', root)

    try:
        parse('y', root)
        assert False
    except ParseError as e:
        assert str(e) == "at 1:1: expected <x>"
