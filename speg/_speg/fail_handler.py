from .errors import ParseError

class _Symbol:
    def __init__(self, parent, parent_height, location, fn):
        self.parent = parent
        self.parent_height = parent_height
        self.location = location
        self.fn = fn

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

class FailHandler:
    def __init__(self, location):
        self.location = location
        self.expected = set()
        self.unexpected = None
        self.unexpected_end_loc = None
        self.sema = []

    def update(self, o):
        assert self.location == o.location
        self.expected.update(o.expected)
        self.sema.append(o.sema)
        if o.unexpected is not None and (self.unexpected is None or self.unexpected_end_loc > o.unexpected_end_loc):
            self.unexpected = o.unexpected
            self.unexpected_end_loc = o.unexpected_end_loc

    def report(self, location, symbol_stack, **kw):
        if self.location > location:
            return False

        if self.location < location:
            self.location = location
            self.expected.clear()
            del self.sema[:]

        for sym in symbol_stack():
            if sym.location != self.location:
                break

        sym_str = _get_fn_name(sym.fn) if sym is not None else None
        self._do_report(sym_str, **kw)

    def _do_report(self, sym_str, message=None, expected=None, unexpected=None):
        if expected is not None:
            self.expected.add(sym_str or expected)
        if unexpected is not None:
            end_loc, fn = unexpected
            if self.unexpected is None or self.unexpected_end_loc > end_loc:
                self.unexpected = _get_fn_name(fn)
                self.unexpected_end_loc = end_loc
        if message is not None:
            self.sema.append(message)

    def clone(self):
        return FailHandler(self.location)

    def parse_error(self, text):
        end_loc = self.location

        msg = []
        for sema in self.sema:
            msg.extend(str(x) for x in sema)

        if self.unexpected is not None:
            msg.append('unexpected {}'.format(self.unexpected))
            end_loc = self.unexpected_end_loc

        exp = sorted(self.expected)
        if len(exp) == 1:
            msg.append('expected {}'.format(exp[0]))
        elif len(exp) > 1:
            msg.append('expected {} or {}'.format(', '.join(exp[:-1]), exp[-1]))

        if not msg:
            msg.append('failed')

        return ParseError('; '.join(msg), text, self.location, end_loc)

