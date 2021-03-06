from speg import Parser, peg, parse, ParseError, eof, hidden
import pytest

def test_simple():
    assert peg("", "") == ""

    assert peg("test", "") == ""
    assert peg("test", "t") == "t"
    assert peg("test", "te") == "te"

def test_position():
    def root(p):
        pp = p.position()
        assert pp.offset == 0
        assert pp.line == 1
        assert pp.col == 1

        p("li")
        pp = p.position()
        assert pp.offset == 2
        assert pp.line == 1
        assert pp.col == 3

        p('ne1\nl')
        pp = p.position()
        assert pp.offset == 7
        assert pp.line == 2
        assert pp.col == 2

    peg("line1\nline2\n", root)

def test_literal_consume():
    def root(p):
        n = p.consume("")
        assert n.value == ""
        assert n.start_pos.offset == 0
        assert n.end_pos.offset == 0

        n = p.consume("te")
        assert n.value == "te"
        assert n.start_pos.offset == 0
        assert n.end_pos.offset == 2

    peg("test", root)

def test_rule_consume():
    def rule(p):
        return p(r'..'), p(r'..')

    def root(p):
        n = p.consume(rule)
        assert n.value == ('te', 'st')
        assert n.end_pos.offset == 4

    peg("test", root)

def test_consume_re():
    def root(p):
        n = p.consume(r'[123]*')
        assert n.value == '31'
        assert n.end_pos.offset == 2

    peg("3141569", root)

def test_simple_fail():
    with pytest.raises(ParseError):
        peg("", "t")

def test_simple_rule():
    def root(p):
        return 2 * p("t")
    assert peg("test", root) == "tt"

def test_eof():
    def root(p):
        p(p.eof)
    assert peg("", root) is None

def test_failed_eof():
    def root(p):
        p('x')
        p(eof)
    try:
        peg("xx", root)
    except ParseError as e:
        assert e.message == 'expected eof'
        assert e.start_pos.offset == 1
        assert e.end_pos.offset == 1

def test_parser():
    p = Parser("text")

    assert p("") == ""
    assert p("te") == "te"
    assert p(r'...') == "tex"

def test_error():
    def root(p):
        p('te')
        p('xx')

    try:
        parse("test", root)
        assert False
    except ParseError as e:
        assert e.start_pos.offset == 2
        assert e.end_pos.offset == 2

def test_sema_error():
    def root(p):
        p('te')
        p.error()

    with pytest.raises(ParseError):
        parse("test", root)

def test_not():
    def ident(p):
        p.not_('[0-9]')
        return p('[_a-zA-Z0-9]+')

    def num(p):
        r = p(r'[0-9]+')
        p.not_(ident)
        return int(r, 10)

    assert parse('123', num).value == 123

    try:
        parse('123a', num)
        assert False
    except ParseError as e:
        assert e.message == 'unexpected <ident>'
        assert e.start_pos.offset == 3
        assert e.end_pos.offset == 4

def test_error_priority():
    def root(p):
        with p:
            return p(num)
        return p(undef)

    def num(p):
        r = p(r'[0-9]+')
        p('s')
        return int(r, 10)

    def undef(p):
        p('x')

    try:
        parse("t", root)
        assert False
    except ParseError as e:
        assert e.start_pos.offset == 0

    try:
        parse("1", root)
        assert False
    except ParseError as e:
        assert e.start_pos.offset == 1

def test_repr():
    def root(p):
        assert repr(p) == "<speg.ParsingState at '*test'>"
        p('te')
        assert repr(p) == "<speg.ParsingState at 'te*st'>"

    parse('test', root)

def test_error_str():
    try:
        parse('test', 'xx')
        assert False
    except ParseError as e:
        assert str(e).startswith('at')

def test_multiple_exp_fails():
    def operator(p):
        return p(r'[+\-]')

    def atom_expr(p):
        with p:
            p(r'\(')
            p(bin_expr)
            return p(r'\)')
        p(r'[0-9]+')

    def bin_expr(p):
        p(atom_expr)
        with p:
            p(operator)
            p(bin_expr)

    def root(p):
        p(bin_expr)
        p(eof)

    try:
        parse('1(', root)
        assert False
    except ParseError as e:
        assert e.message == 'expected one of <operator>, eof'

def test_hidden_rule():
    def x(p):
        p('x')

    def root(p):
        p(x)
        p(eof)

    try:
        parse('y', root)
    except ParseError as e:
        assert e.message == 'expected <root>'

    root = hidden(root)

    try:
        parse('y', root)
    except ParseError as e:
        assert e.message == 'expected <x>'

def test_opt():
    def ws(p):
        p(r' +')

    def x(p):
        p(r'x')

    @hidden
    def root(p):
        p.opt(ws)
        p(x)

    parse('  x', root)
    parse('x', root)

    try:
        parse('y', root)
        assert False
    except ParseError as e:
        assert e.message == 'expected one of <ws>, <x>'
