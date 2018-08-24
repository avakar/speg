from .errors import ParseError
from .peg import parse, parser

def hidden(fn):
    fn._speg_hidden = True
    return fn
