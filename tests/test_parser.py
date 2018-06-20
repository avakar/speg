from speg import peg, ParseError
import pytest

def test_simple():
    assert peg("", "") == ""

    assert peg("test", "") == ""
    assert peg("test", "t") == "t"
    assert peg("test", "te") == "te"

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
