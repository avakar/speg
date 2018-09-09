import six
from collections import defaultdict
from .errors import ParseError, Diagnostic

def _get_fn_name(fn):
    n = getattr(fn, '__doc__', None)
    if n is None:
        n = fn.__name__
        n = n.replace('_', ' ').strip()
        return '<{}>'.format(n)

    try:
        n = n[:n.index('\n')]
    except ValueError:
        pass
    return n.strip()

_lvl_expected = 0
_lvl_unexpected = 1
_lvl_sema = 2

def _update_optdict(dest, src):
    if dest is None:
        return src
    if src is None:
        return dest

    for k, v in six.iteritems(src):
        dest[k].update(v)
    return dest

def _add_optdict(d, k, v):
    if d is None:
        d = defaultdict(lambda: set())
    d[k].add(v)
    return d

def _format_symset(symset):
    assert symset
    return ', '.join(symset)

class FailInfo:
    def __init__(self):
        self._expected = None
        self._unexpected = None
        self._sema = None

    def update_from(self, o):
        self._expected = _update_optdict(self._expected, o._expected)
        self._unexpected = _update_optdict(self._unexpected, o._unexpected)
        self._sema = _update_optdict(self._sema, o._sema)

    def report(self, fn_desc, message=None, expected=None, unexpected=None, ranges=()):
        ranges = frozenset(ranges)
        if message is not None:
            self._sema = _add_optdict(self._sema, ranges, message)
        elif unexpected is not None:
            self._unexpected = _add_optdict(self._unexpected, ranges, _get_fn_name(unexpected))
        elif expected is not None:
            self._expected = _add_optdict(self._expected, ranges, fn_desc or expected)

    def parse_error(self, location, text):
        diags = []
        if self._sema:
            diags.extend(Diagnostic(message, location, ranges) for ranges, message_set in six.iteritems(self._sema) for message in message_set)
        if self._unexpected:
            diags.extend(Diagnostic('unexpected {}'.format(_format_symset(symset)), location, ranges) for ranges, symset in six.iteritems(self._unexpected))
        if self._expected:
            diags.extend(Diagnostic('expected {}'.format(_format_symset(symset)), location, ranges) for ranges, symset in six.iteritems(self._expected))
        return ParseError(diags, text)

class FailHandler:
    def __init__(self, location):
        self._location = location
        self._info = None

    def update_from(self, o):
        if self._location < o._location:
            self._info = o._info
            self._location = o._location
        elif self._location == o._location:
            if self._info is None:
                self._info = o._info
            elif o._info is not None:
                self._info.update_from(o._info)
        o._info = None

    def report(self, location, symbol_stack, **kw):
        if self._location > location:
            return False

        if self._location < location:
            self._location = location
            self._info = None

        current_fn = None
        for fn, location in symbol_stack():
            if location != self._location:
                break
            else:
                current_fn = fn

        fn_desc = _get_fn_name(current_fn) if current_fn is not None else None
        if self._info is None:
            self._info = FailInfo()
        self._info.report(fn_desc, **kw)

    def clone(self):
        return FailHandler(self._location)

    def parse_error(self, text):
        assert self._info is not None
        return self._info.parse_error(self._location, text)
