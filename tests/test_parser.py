from speg import prepare, peg, ParseError
import pytest

def test_simple():
    assert peg("", "") == ""

    assert peg("test", "") == ""
    assert peg("test", "t") == "t"
    assert peg("test", "te") == "te"

def test_position():
    p = prepare("line1\nline2\n")

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

def test_literal_consume():
    p = prepare("test")

    n = p.consume("")
    assert n.value == ""
    assert n.start_pos.offset == 0
    assert n.end_pos.offset == 0

    n = p.consume("te")
    assert n.value == "te"
    assert n.start_pos.offset == 0
    assert n.end_pos.offset == 2

def test_rule_consume():
    def root(p):
        return p(r'..'), p(r'..')

    p = prepare("test")
    n = p.consume(root)
    assert n.value == ('te', 'st')
    assert n.end_pos.offset == 4

def test_consume_re():
    p = prepare("3141569")
    n = p.consume(r'[123]*')
    assert n.value == '31'
    assert n.end_pos.offset == 2

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
