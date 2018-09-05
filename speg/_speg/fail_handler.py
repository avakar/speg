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

class FailInfo:
    def __init__(self):
        self.expected = set()
        self.unexpected = None
        self.unexpected_end_loc = None
        self.sema = []

    def clear(self):
        self.expected.clear()
        del self.sema[:]
        self.unexpected = None

    def update_from(self, o):
        self.expected.update(o.expected)
        self.sema.append(o.sema)
        if o.unexpected is not None and (
            self.unexpected is None or self.unexpected_end_loc > o.unexpected_end_loc
            ):
            self.unexpected = o.unexpected
            self.unexpected_end_loc = o.unexpected_end_loc

    def report(self, fn_desc, message=None, expected=None, unexpected=None):
        if expected is not None:
            self.expected.add(fn_desc or expected)
        if unexpected is not None:
            end_loc, fn = unexpected
            if self.unexpected is None or self.unexpected_end_loc > end_loc:
                self.unexpected = _get_fn_name(fn)
                self.unexpected_end_loc = end_loc
        if message is not None:
            self.sema.append(message)

    def parse_error(self, location, text):
        end_loc = location

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

        return ParseError('; '.join(msg), text, location, end_loc)

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
            if self._info is not None:
                self._info.clear()

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
        assert self._info
        return self._info.parse_error(self._location, text)

