from speg import parse, ParseError, re

@re(r'[0-9]+')
def _number(s):
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
        r = p.parse(_expression)
        p.eat(')')
        return r
    return p.parse(_number)

def _expression(p):
    lhs = p.parse(_atom)
    while p:
        with p:
            op = p.parse(_operator)
            rhs = p.parse(_atom)
            lhs = op(lhs, rhs)

    return lhs

def evaluate_expr(text):
    return parse(text, _expression)

def test_example():
    assert evaluate_expr('2+2') == 4
    assert evaluate_expr('2-(1+1)') == 0

    try:
        evaluate_expr('2-(1+1')
    except ParseError as e:
        assert str(e) == "at 1:7: expected ')' or <operator>"

    try:
        evaluate_expr('2*2')
    except ParseError as e:
        assert str(e) == "at 1:2: expected <operator> or end of input"

    try:
        evaluate_expr('2+(-2)')
    except ParseError as e:
        assert str(e) == 'at 1:4: expected <expression>'
