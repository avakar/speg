import re
import sys

import six

from .errors import FailHandler
from .position import Location, get_line_at_location

class _ParseBacktrackError(BaseException):
    pass

def parse(text, fn, initial_location=Location()):
    fail_handler = FailHandler(initial_location)
    p = Parser(text, fail_handler, initial_location)
    try:
        return p.parse(fn)
    except _ParseBacktrackError:
        raise fail_handler.parse_error(text)

from functools import wraps

def matcher(fn):
    mm = fn()

    @wraps(fn)
    def call(p):
        m = mm.match(p.tail())
        if not m:
            p.fail()
        else:
            assert m.start() == 0
            return p.skip(m.end())
    return call

class _OptProxy:
    def __init__(self, p):
        self._p = p

    def check_eof(self):
        with self:
            return self._p.check_eof()
        return ''

    def eat(self, s):
        with self:
            return self._p.eat(s)
        return ''

    def parse(self, r):
        with self:
            return self._p(r)
        return ''

    def __enter__(self):
        self._p._fail_handler.push_suppress()
        r = self._p.__enter__()
        return r

    def __exit__(self, type, value, traceback):
        r = self._p.__exit__(type, value, traceback)
        self._p._fail_handler.pop_suppress()
        self._p.clear()
        return r

class _VarStackEntry:
    def __init__(self):
        self.map = {}
        self.depth = 0

class Parser(object):
    def __init__(self, s, fail_handler, initial_location):
        self._s = s
        self._fail_handler = fail_handler
        self._location_stack = [initial_location]
        self._var_stack = [_VarStackEntry()]

        self._succeeded = True

        self.opt = _OptProxy(self)

    @property
    def index(self):
        return self.location.index

    @property
    def location(self):
        return self._location_stack[-1]

    def check_eof(self):
        loc = self._location_stack[-1]
        if loc.index != len(self._s):
            self._fail_handler.report(loc, expected='end of input')
            raise _ParseBacktrackError()
        return self._s[loc.index:loc.index]

    def tail(self):
        return self._s[self.index:]

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
            self._fail_handler.report(loc, expected=repr(s))
            raise _ParseBacktrackError()
        self._location_stack[-1] = loc.after(s)
        return s

    def parse(self, fn):
        self._fail_handler.push_symbol(self.location, fn)
        var_entry = self._var_stack[-1]
        var_entry.depth += 1

        try:
            self._succeeded = True
            r = fn(self)
            self._succeeded = True
            return r
        finally:
            while self._var_stack[-1].depth == 0:
                self._var_stack.pop()
            self._var_stack[-1].depth -= 1
            self._fail_handler.pop_symbol()

    def fail(self, **kw):
        self._fail_handler.report(self.location, **kw)
        raise _ParseBacktrackError()

    def get(self, key, default=None):
        for entry in self._var_stack:
            if key in entry.map:
                return entry.map[key]
        return default

    def __getitem__(self, key):
        for entry in self._var_stack:
            if key in entry.map:
                return entry.map[key]
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        entry = self._var_stack[-1]
        if entry.depth == 0:
            entry.map[key] = value
        else:
            entry = _VarStackEntry()
            self._var_stack.append(entry)

    def __repr__(self):
        line, line_offs = get_line_at_location(self._s, self._location_stack[-1])
        return '<speg.ParsingState at {!r}>'.format('{}*{}'.format(line[:line_offs], line[line_offs:]))

    # def not_(self, r, *args, **kw):
    #     start_loc = self.location
    #     self._states.append(_State(start_loc))
    #     self._fail_handler.push_suppress()
    #     try:
    #         self.parse(r)
    #     except _ParseBacktrackError:
    #         consumed = False
    #     else:
    #         end_loc = self.location
    #         consumed = True
    #     finally:
    #         self._fail_handler.pop_suppress()
    #         self._states.pop()

    #     if consumed:
    #         self._fail_handler.unexpected_symbol(start_loc, end_loc, r)
    #         raise _ParseBacktrackError
    #     return ''

    def __enter__(self):
        loc = self._location_stack[-1]
        self._location_stack.append(loc)
        self._fail_handler.push_state(loc)

    def __exit__(self, type, value, traceback):
        self._succeeded = type is None
        self._fail_handler.pop_state(self._succeeded)

        if self._succeeded:
            self._location_stack[-2] = self._location_stack[-1]

        self._location_stack.pop()
        return type is _ParseBacktrackError

    def clear(self):
        self._succeeded = True

    def __nonzero__(self):
        return self._succeeded

    __bool__ = __nonzero__
