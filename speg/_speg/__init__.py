from functools import wraps
import re as _py_re

from .parser import Parser
from .errors import ParseBacktrackError
from .fail_handler import FailHandler
from .position import Location

def parse(text, fn, initial_location=Location(), fail_handler=None):
    if fail_handler is None:
        fail_handler = FailHandler(initial_location)
    p = Parser(text, fail_handler, initial_location)
    try:
        return p.parse(fn)
    except ParseBacktrackError:
        raise fail_handler.parse_error(text)

def re(pattern, flags=0):
    compiled = _py_re.compile(pattern, flags)

    def decorator(fn):
        @wraps(fn)
        def parse(p):
            m = compiled.match(p.tail)
            if not m:
                p.fail(expected=repr(compiled))
            s = p.skip(m.end())
            return fn(s)
        return parse
    return decorator

def hidden(fn):
    fn._speg_hidden = True
    return fn
