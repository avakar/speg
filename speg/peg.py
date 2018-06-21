import re
import sys

import six

from .position import Position

class ParseError(Exception):
    def __init__(self, msg, text, position):
        self.msg = msg
        self.text = text
        self.position = position
        super(ParseError, self).__init__(msg, text, position)

def peg(text, root_rule):
    p = _Peg(text)
    try:
        return p(root_rule)
    except _UnexpectedError:
        idx = max(p._errors)
        err = p._errors[idx]
        raise ParseError(err.msg, text, err.pos)

def prepare(text):
    return _Peg(text)

class _UnexpectedError(RuntimeError):
    def __init__(self, state, expr):
        self.state = state
        self.expr = expr

class _PegState:
    def __init__(self, idx, pos):
        self.idx = idx
        self.pos = pos
        self.vars = {}
        self.committed = False

class _PegError:
    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

class Node:
    def __init__(self, value, start_pos, end_pos):
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

class _Peg:
    def __init__(self, s, position=Position.initial()):
        self._s = s
        self._states = [_PegState(0, position)]
        self._errors = {}
        self._re_cache = {}

    def __call__(self, r, *args, **kw):
        if isinstance(r, six.string_types):
            flags = args[0] if args else 0
            compiled = self._re_cache.get((r, flags))
            if not compiled:
                compiled = re.compile(r, flags)
                self._re_cache[r, flags] = compiled
            st = self._states[-1]
            m = compiled.match(self._s[st.idx:])
            if not m:
                self.error(expr=r, err=kw.get('err'))

            ms = m.group(0)
            st.idx += len(ms)
            st.pos = st.pos.update(ms)
            return ms
        else:
            kw.pop('err', None)
            return r(self, *args, **kw)

    def consume(self, r, *args, **kw):
        start_pos = self.position()
        value = self(r, *args, **kw)
        end_pos = self.position()
        return Node(value, start_pos, end_pos)

    def position(self):
        return self._states[-1].pos

    def __repr__(self):
        idx = self._states[-1].idx
        vars = {}
        for st in self._states:
            vars.update(st.vars)
        return '_Peg(%r, %r)' % (self._s[:idx] + '*' + self._s[idx:], vars)

    @staticmethod
    def eof(p):
        if p._states[-1].idx != len(p._s):
            p.error()

    def error(self, err=None, expr=None):
        st = self._states[-1]
        if err is None:
            err = 'expected {!r}, found {!r}'.format(expr, self._s[st.idx:st.idx+4])
        self._errors[st.idx] = _PegError(err, st.idx)
        raise _UnexpectedError(st, expr)

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

    def not_(self, s, *args, **kw):
        with self:
            self(s)
            self.error()

    def __enter__(self):
        self._states[-1].committed = False
        self._states.append(_PegState(self._states[-1].idx, self._states[-1].pos))

    def __exit__(self, type, value, traceback):
        if type is None:
            self.commit()
        self._states.pop()
        return type == _UnexpectedError

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

        prev.pos = cur.pos
        prev.committed = True

    def __nonzero__(self):
        return self._states[-1].committed

    __bool__ = __nonzero__
