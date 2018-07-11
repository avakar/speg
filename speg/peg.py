import re
import sys

import six

from .errors import ExpectedExprError, UnexpectedExprError, SemanticError
from .position import Position, get_line_at_position

class Eof: pass
eof = Eof()

class _ParseBacktrackError(BaseException):
    pass

class _PegState:
    def __init__(self, position):
        self.position = position
        self.vars = {}
        self.committed = False
        self.error = None
        self.error_idx = None

    def update_error(self, exc, idx):
        if self.error is None or self.error_idx < idx:
            self.error = exc
            self.error_idx = idx

class Node:
    def __init__(self, value, start_pos, end_pos):
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

class Parser:
    def __init__(self, text):
        self._text = text

    def __call__(self, r, *args, **kw):
        return self._parse(lambda p: p(r, *args, **kw))

    def parse(self, r, *args, **kw):
        return self._parse(lambda p: p.consume(r, *args, **kw))

    def _parse(self, fn):
        p = ParsingState(self._text)
        try:
            return fn(p)
        except _ParseBacktrackError:
            assert len(p._states) == 1
            raise p._states[0].error

class CallstackEntry:
    def __init__(self, position, fn, args, kw):
        self.position = position
        self.fn = fn
        self.args = args
        self.kw = kw

class ParsingState(object):
    def __init__(self, s):
        self._s = s
        self._states = [_PegState(Position())]
        self._re_cache = {}
        self._callstack = []

    def __call__(self, r, *args, **kw):
        st = self._states[-1]
        if r is eof:
            if st.position.offset != len(self._s):
                self._raise(ExpectedExprError(self._s, st.position, tuple(self._callstack), eof))
            return ''
        elif isinstance(r, six.string_types):
            flags = args[0] if args else 0
            compiled = self._re_cache.get((r, flags))
            if not compiled:
                compiled = re.compile(r, flags)
                self._re_cache[r, flags] = compiled
            m = compiled.match(self._s[st.position.offset:])
            if not m:
                self._raise(ExpectedExprError(self._s, st.position, tuple(self._callstack), r))

            ms = m.group(0)
            st.position = st.position.advanced_by(ms)
            return ms
        else:
            kw.pop('err', None)
            self._callstack.append(CallstackEntry(st.position, r, args, kw))
            try:
                return r(self, *args, **kw)
            finally:
                self._callstack.pop()

    def consume(self, r, *args, **kw):
        start_pos = self.position()
        value = self(r, *args, **kw)
        end_pos = self.position()
        return Node(value, start_pos, end_pos)

    def position(self):
        return self._states[-1].position

    def __repr__(self):
        line, line_offs = get_line_at_position(self._s, self._states[-1].position)
        return '<speg.ParsingState at {!r}>'.format('{}*{}'.format(line[:line_offs], line[line_offs:]))

    @staticmethod
    def eof(p):
        return p(eof)

    def error(self, *args, **kw):
        st = self._states[-1]
        exc = SemanticError(self._s, st.position, tuple(self._callstack), args, kw)
        self._raise(exc)

    def _raise(self, exc):
        st = self._states[-1]
        st.update_error(exc, st.position.offset)
        raise _ParseBacktrackError()

    def get(self, key, default=None):
        for state in self._states[::-1]:
            if key in state.vars:
                return state.vars[key][0]
        return default

    def set(self, key, value):
        self._states[-1].vars[key] = value, False

    def set_global(self, key, value):
        self._states[-1].vars[key] = value, True

    def opt(self, *args, **kw):
        with self:
            return self(*args, **kw)

    def not_(self, r, *args, **kw):
        with self:
            n = self.consume(r)
        if self:
            self._raise(UnexpectedExprError(self._s, n.start_pos, n.end_pos, tuple(self._callstack), r))

    def __enter__(self):
        self._states[-1].committed = False
        self._states.append(_PegState(self._states[-1].position))

    def __exit__(self, type, value, traceback):
        if type is None:
            self.commit()
        else:
            cur = self._states[-1]
            prev = self._states[-2]
            if cur.error:
                prev.update_error(cur.error, cur.error_idx)

        self._states.pop()
        return type is _ParseBacktrackError

    def commit(self):
        cur = self._states[-1]
        prev = self._states[-2]

        for key in cur.vars:
            val, g = cur.vars[key]
            if not g:
                continue
            if key in prev.vars:
                prev.vars[key] = val, prev.vars[key][1]
            else:
                prev.vars[key] = val, True

        cur.error = None
        cur.error_idx = None

        prev.position = cur.position
        prev.committed = True

    def __nonzero__(self):
        return self._states[-1].committed

    __bool__ = __nonzero__
