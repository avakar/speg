from ._speg.errors import ParseError
from ._speg.peg import parse, parser, matcher
from ._speg.position import Location

def hidden(fn):
    fn._speg_hidden = True
    return fn
