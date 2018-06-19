from speg import peg

def test_consume():
    assert peg("test", "te") == "te"
