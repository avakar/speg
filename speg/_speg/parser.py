import inspect

from .errors import ParseBacktrackError
from .position import Location, get_line_at_location

class _OptProxy:
    def __init__(self, p):
        self._p = p

    def check_eof(self):
        with self:
            return self._p.check_eof()
        return self._p.tail[:0]

    def eat(self, s):
        with self:
            return self._p.eat(s)
        return self._p.tail[:0]

    def parse(self, r):
        with self:
            return self._p(r)
        return self._p.tail[:0]

    def __enter__(self):
        self._p._opt_level += 1
        return self._p.__enter__()

    def __exit__(self, type, value, traceback):
        r = self._p.__exit__(type, value, traceback)
        self._p._opt_level -= 1
        self._p.clear()
        return r

class _SymStackEntry:
    def __init__(self, sym):
        self.sym = sym
        self.var_map = None

class Parser(object):
    def __init__(self, s, fail_handler, initial_location):
        self._s = s
        self._fail_handler = fail_handler
        self._location_stack = [initial_location]
        self._sym_stack = [_SymStackEntry(None)]

        self._succeeded = True

        self._opt_level = 0
        self.opt = _OptProxy(self)

    @property
    def index(self):
        return self.location.index

    @property
    def location(self):
        return self._location_stack[-1]

    @property
    def tail(self):
        return self._s[self.index:]

    def check_eof(self):
        loc = self._location_stack[-1]
        if loc.index != len(self._s):
            self.fail(expected='end of input')
        return self._s[loc.index:loc.index]

    def skip(self, n):
        loc = self._location_stack[-1]
        idx = loc.index
        s = self._s[idx:idx+n]
        self._location_stack[-1] = loc.after(s)
        return s

    def eat(self, s):
        loc = self._location_stack[-1]
        idx = loc.index
        l = len(s)
        if self._s[idx:idx+l] != s:
            self.fail(expected=repr(s))
        self._location_stack[-1] = loc.after(s)
        return s

    def parse(self, fn):
        if not self._opt_level:
            self._fail_handler.push_symbol(self.location, fn)
        var_entry = self._sym_stack[-1]
        var_entry.depth += 1

        try:
            self._succeeded = True
            r = fn(self)
            self._succeeded = True
            return r
        finally:
            while self._sym_stack[-1].depth == 0:
                self._sym_stack.pop()
            self._sym_stack[-1].depth -= 1
            if not self._opt_level:
                self._fail_handler.pop_symbol()
    parse._speg_parse_stack_entry = True

    def fail(self, message=None, **kw):
        if not self._opt_level:
            self._fail_handler.report(self.location, self.symbol_stack, message=message, **kw)
        raise ParseBacktrackError()

    def get(self, key, default=None):
        for entry in self._sym_stack:
            if key in entry.map:
                return entry.map[key]
        return default

    def __getitem__(self, key):
        for entry in self._sym_stack:
            if key in entry.map:
                return entry.map[key]
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        entry = self._sym_stack[-1]
        if entry.depth == 0:
            entry.map[key] = value
        else:
            entry = _SymStackEntry()
            self._sym_stack.append(entry)

    def __repr__(self):
        line, line_offs = get_line_at_location(self._s, self._location_stack[-1])
        return '<speg.ParsingState at {!r}>'.format('{}*{}'.format(line[:line_offs], line[line_offs:]))

    # def not_(self, r, *args, **kw):
    #     start_loc = self.location
    #     self._states.append(_State(start_loc))
    #     try:
    #         self.parse(r)
    #     except _ParseBacktrackError:
    #         consumed = False
    #     else:
    #         end_loc = self.location
    #         consumed = True
    #     finally:
    #         self._states.pop()

    #     if consumed:
    #         self._fail_handler.unexpected_symbol(start_loc, end_loc, r)
    #         raise _ParseBacktrackError
    #     return ''

    def __enter__(self):
        loc = self._location_stack[-1]
        self._location_stack.append(loc)
        if not self._opt_level:
            self._fail_handler.push_state(loc)

    def __exit__(self, type, value, traceback):
        self._succeeded = type is None

        if not self._opt_level:
            self._fail_handler.pop_state(self._succeeded)

        if self._succeeded:
            self._location_stack[-2] = self._location_stack[-1]
        self._location_stack.pop()
        return type is ParseBacktrackError

    def clear(self):
        self._succeeded = True

    def __nonzero__(self):
        return self._succeeded

    __bool__ = __nonzero__

    @property
    def symbol_stack(self):
        cur = inspect.currentframe()
        while cur is not None:
            while cur is not None and (cur.f_code is not self.parse.__code__ or cur.f_locals['self'] is not self):
                cur = cur.f_back
            yield cur.f_locals['fn']
