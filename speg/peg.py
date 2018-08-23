from contextlib import contextmanager
import re
import sys

import six

from .errors import FailHandler
from .position import Location, get_line_at_position

class _ParseBacktrackError(BaseException):
    pass

@contextmanager
def parser(text):
    fail_handler = FailHandler(Location()) # XXX location to parsingstate too
    p = ParsingState(text, fail_handler)
    try:
        yield p
    except _ParseBacktrackError:
        raise fail_handler.parse_error(text)

def parse(text, fn, *args, **kw):
    with parser(text) as p:
        return p(fn, *args, **kw)

class _State:
    def __init__(self, location=Location()):
        self.location = location
        self.vars = None

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

    def match(self, pattern):
        with self:
            return self._p.match(pattern)
        return ''

    def re(self, pattern, flags=0):
        with self:
            return self._p.re(pattern, flags)
        return ''

    def __call__(self, r, *args, **kw):
        with self:
            return self._p(r, *args, **kw)
        return ''

    def __enter__(self):
        r = self._p.__enter__()
        self._p._fail_handler.suppress_fails()
        return r

    def __exit__(self, type, value, traceback):
        return self._p.__exit__(type, value, traceback)

# class _NotProxy:
#     def __init__(self, p):
#         self._p = p

#     def check_eof(self):
#         with self._p:
#             self._p.check_eof()
#         return ''

#     def eat(self, s):
#         with self:
#             self._p.eat(s)
#         return ''

#     def match(self, pattern):
#         with self:
#             self._p.match(pattern)
#         return ''

#     def re(self, pattern, flags=0):
#         with self:
#             self._p.re(pattern, flags)
#         return ''

#     def __call__(self, r, *args, **kw):
#         with self._p:
#             return self._p(r, *args, **kw)
#         return ''

class ParsingState(object):
    def __init__(self, s, fail_handler):
        self._s = s
        self._states = [_State()]
        self._re_cache = {}
        self._fail_handler = fail_handler

        self._succeeded = True

        self.opt = _OptProxy(self)
        #self.not_ = _NotProxy(self)

    @property
    def index(self):
        return self.location.index

    @property
    def location(self):
        return self._states[-1].location

    def check_eof(self):
        st = self._states[-1]
        if st.location.index != len(self._s):
            self._fail_handler.expected_eof(st.location)
            raise _ParseBacktrackError()
        return ''

    def eat(self, s):
        st = self._states[-1]
        idx = st.location.index
        l = len(s)
        if self._s[idx:idx+l] != s:
            self._fail_handler.expected_string(st.location, s)
            raise _ParseBacktrackError()
        st.location = st.location.advanced_by(s)
        return s

    def match(self, pattern):
        st = self._states[-1]
        idx = st.location.index
        m = pattern.match(self._s[idx:])
        if not m:
            self._fail_handler.expected_match(st.location, pattern)
            raise _ParseBacktrackError()
        s = m.group()
        st.location = st.location.advanced_by(s)
        return s

    def re(self, pattern, flags=0):
        k = pattern, flags
        compiled = self._re_cache.get(k)
        if compiled is None:
            compiled = re.compile(pattern, flags)
            self._re_cache[k] = compiled
        return self.match(compiled)

    def __call__(self, fn, *args, **kw):
        self._fail_handler.push_symbol(self.location, fn, args, kw)
        try:
            self._succeeded = True
            r = fn(self, *args, **kw)
            self._succeeded = True
            return r
        finally:
            self._fail_handler.pop_symbol()

    def fail(self, *args, **kw):
        self._fail_handler.explicit_fail(self.location, args, kw)
        raise _ParseBacktrackError()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        for state in self._states[::-1]:
            if state.vars is not None and key in state.vars:
                return state.vars[key]
        raise KeyError('{}'.format(key))

    def __setitem__(self, key, value):
        st = self._states[-1]
        if st.vars is None:
            st.vars = { key: value }
        else:
            st.vars[key] = value

    def __repr__(self):
        line, line_offs = get_line_at_position(self._s, self._states[-1].location)
        return '<speg.ParsingState at {!r}>'.format('{}*{}'.format(line[:line_offs], line[line_offs:]))

    def not_(self, fn, *args, **kw):
        st = self._states[-1]
        self._states.append(_State(st.location))

        self._fail_handler.push_state(st.location)
        self._fail_handler.suppress_fails()

        try:
            self(fn, *args, **kw)
        except _ParseBacktrackError:
            self._succeeded = True
            self._fail_handler.pop_state(True)
            self._states.pop()
            return ''


        else:
            self._fail_handler


    # def not_(self, r, *args, **kw):
    #     self._states.append(_State(self._states[-1].position))
    #     try:
    #         n = self.consume(r)
    #     except _ParseBacktrackError:
    #         consumed = False
    #     else:
    #         consumed = True
    #     finally:
    #         self._states.pop()

    #     if consumed:
    #         self._raise(UnexpectedExpr, n.end_pos, r)

    def __enter__(self):
        st = self._states[-1]
        self._states.append(_State(st.location))

        self._fail_handler.push_state(st.location)

    def __exit__(self, type, value, traceback):
        self._succeeded = type is None
        self._fail_handler.pop_state(self._succeeded)

        if self._succeeded:
            self._states[-2].location = self._states[-1].location

        self._states.pop()
        return type is _ParseBacktrackError

    def __nonzero__(self):
        return self._succeeded

    __bool__ = __nonzero__
