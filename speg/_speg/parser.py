import inspect

from .errors import ParseBacktrackError
from .position import Location, get_line_at_location

class Parser(object):
    def __init__(self, s, fail_handler, initial_location):
        self._s = s

        self._sym = _Sym(None, initial_location, None)
        self._vars_sym = None

        self._context = _Context(initial_location, fail_handler, None)
        self._last_fail_ctx = self._context

        self._succeeded = True

        self.opt = _OptProxy(self)
        self.vars = _VarsProxy(self)

    @property
    def index(self):
        return self.location.index

    @property
    def location(self):
        return self._context.location

    @property
    def tail(self):
        return self._s[self.index:]

    def check_eof(self):
        loc = self._context.location
        if loc.index != len(self._s):
            self.fail(expected='end of input')
        return self._s[loc.index:loc.index]

    def skip(self, n):
        loc = self._context.location
        idx = loc.index
        s = self._s[idx:idx+n]
        self._context.location = loc.after(s)
        return s

    def eat(self, s):
        loc = self._context.location
        idx = loc.index
        l = len(s)
        if self._s[idx:idx+l] != s:
            self.fail(expected=repr(s))
        self._context.location = loc.after(s)
        return s

    def parse(self, fn):
        self._sym = _Sym(fn, self.location, self._sym)
        try:
            self._succeeded = True
            r = fn(self)
            self._succeeded = True
            return r
        finally:
            self._sym = self._sym.parent

    def fail(self, message=None, **kw):
        if self._context.fail_ctx is None:
            self._context.fail_ctx = self._last_fail_ctx.fail_ctx.clone()
            self._last_fail_ctx = self._context
        self._context.fail_ctx.report(self.location, self._symbols, message=message, **kw)
        raise ParseBacktrackError()

    def __repr__(self):
        line, line_offs = get_line_at_location(self._s, self._context.location)
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
        loc = self._context.location
        self._context = _Context(loc, None, self._context)

    def __exit__(self, type, value, traceback):
        self._succeeded = type is None

        ctx = self._context
        self._context = ctx.parent

        if self._succeeded:
            self._context.update(ctx)

        return type is ParseBacktrackError

    def clear(self):
        self._succeeded = True

    def __nonzero__(self):
        return self._succeeded

    __bool__ = __nonzero__

    def _symbols(self):
        cur = self._sym
        while cur is not None:
            yield cur
            cur = cur.parent

class _Sym:
    def __init__(self, fn, location, parent):
        self.fn = fn
        self.location = location
        self.parent = parent
        self.vars_parent = None
        self.vars = None

class _Context:
    def __init__(self, location, fail_ctx, parent):
        self.location = location
        self.fail_ctx = fail_ctx
        self.parent = parent

    def update(self, ctx):
        self.location = ctx.location
        if ctx.fail_ctx:
            if self.fail_ctx:
                self.fail_ctx.update(ctx.fail_ctx)
            else:
                self.fail_ctx = ctx.fail_ctx

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

class _VarsProxy:
    def __init__(self, p):
        self._p = p

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        sym = self._p._vars_sym
        while sym is not None:
            assert sym.vars is not None
            if key in sym.vars:
                return sym.vars[key]
            sym = sym.vars_parent
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        sym = self._p._sym
        if sym.vars is None:
            sym.vars = { key: value }
            sym.vars_parent = self._p._vars_sym
            self._p._vars_sym = sym
        else:
            sym.vars[key] = value

    def __iter__(self):
        sym = self._p._vars_sym
        while sym is not None:
            for key in sym.vars:
                yield key
            sym = sym.vars_parent

    def __contains__(self, key):
        sym = self._p._vars_sym
        while sym is not None:
            if key in sym.vars:
                return True
            sym = sym.vars_parent
        return False

    def __len__(self):
        keys = set(self)
        return len(keys)
