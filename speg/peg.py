import re
import sys

import six

class ParseError(Exception):
    def __init__(self, msg, text, offset, line, col):
        self.msg = msg
        self.text = text
        self.offset = offset
        self.line = line
        self.col = col
        super(ParseError, self).__init__(msg, offset, line, col)

def peg(text, root_rule):
    p = _Peg(text)
    try:
        return p(root_rule)
    except _UnexpectedError:
        offset = max(p._errors)
        err = p._errors[offset]
        raise ParseError(err.msg, text, offset, err.line, err.col)

def prepare(text):
    return _Peg(text)

class _UnexpectedError(RuntimeError):
    def __init__(self, state, expr):
        self.state = state
        self.expr = expr

class _PegState:
    def __init__(self, pos, line, col):
        self.pos = pos
        self.line = line
        self.col = col
        self.vars = {}
        self.committed = False

    def position(self):
        return StdPosition(self.pos, self.line, self.col)

class _PegError:
    def __init__(self, msg, line, col):
        self.msg = msg
        self.line = line
        self.col = col

class StdPosition:
    def __init__(self, offset, line, col):
        self.offset = offset
        self.line = line
        self.col = col

class Node:
    def __init__(self, value, start_pos, end_pos):
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

class _Peg:
    def __init__(self, s):
        self._s = s
        self._states = [_PegState(0, 1, 1)]
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
            m = compiled.match(self._s[st.pos:])
            if not m:
                self.error(expr=r, err=kw.get('err'))

            ms = m.group(0)
            st.pos += len(ms)
            nl_pos = ms.rfind('\n')
            if nl_pos < 0:
                st.col += len(ms)
            else:
                st.col = len(ms) - nl_pos
                st.line += ms[:nl_pos].count('\n') + 1
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
        return self._states[-1].position()

    def __repr__(self):
        pos = self._states[-1].pos
        vars = {}
        for st in self._states:
            vars.update(st.vars)
        return '_Peg(%r, %r)' % (self._s[:pos] + '*' + self._s[pos:], vars)

    @staticmethod
    def eof(p):
        if p._states[-1].pos != len(p._s):
            p.error()

    def error(self, err=None, expr=None):
        st = self._states[-1]
        if err is None:
            err = 'expected {!r}, found {!r}'.format(expr, self._s[st.pos:st.pos+4])
        self._errors[st.pos] = _PegError(err, st.line, st.col)
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
        self._states.append(_PegState(self._states[-1].pos, self._states[-1].line, self._states[-1].col))

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
        prev.line = cur.line
        prev.col = cur.col
        prev.committed = True

    def __nonzero__(self):
        return self._states[-1].committed

    __bool__ = __nonzero__
