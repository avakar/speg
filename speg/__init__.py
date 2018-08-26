from ._speg.errors import ParseError
from ._speg.peg import parse, parser
from ._speg.position import Location, get_line_at_position

def hidden(fn):
    fn._speg_hidden = True
    return fn
