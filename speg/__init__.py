from .peg import Parser, eof
from .errors import ParseError, ExpectedExprError, UnexpectedExprError, SemanticError

def peg(text, root_rule):
    p = Parser(text)
    return p(root_rule)

def parse(text, root_rule):
    p = Parser(text)
    return p.parse(root_rule)
