import inspect

from .errors import ParseBacktrackError

class Parser(object):
    """
    The parser keeps two stacks, a symbol stack and a subparser stack.

    The symbol stack starts out empty and a new symbol is pushed on it whenever
    the `parse` function is called.

    The subparser stack starts out with a single item and is appended to
    whenever a new subpaser context is entered (using the `with` statement).
    Each subparser keeps track of the current location and fail info (if any).
    When the subparser finishes, its subparser stack item is merged into its
    parent's. If the subparser succeeded, the fail info is discarded, otherwise
    the location is discarded.
    """

    def __init__(self, s, fail_handler, initial_location):
        self._s = s

        self._sym = None
        self._subparser = _Subparser(initial_location, fail_handler, None)

        self._succeeded = True

        self.opt = _OptProxy(self)
        self.vars = _VarsProxy(self)

    @property
    def index(self):
        return self.location.index

    @property
    def location(self):
        return self._subparser.location

    @property
    def tail(self):
        return self._s[self.index:]

    def check_eof(self):
        loc = self._subparser.location
        if loc.index != len(self._s):
            self.fail(expected='end of input')
        return self._s[loc.index:loc.index]

    def skip(self, n):
        loc = self._subparser.location
        idx = loc.index
        s = self._s[idx:idx+n]
        self._subparser.location = loc.after(s)
        return s

    def eat(self, s):
        loc = self._subparser.location
        idx = loc.index
        l = len(s)
        if self._s[idx:idx+l] != s:
            self.fail(expected=repr(s))
        self._subparser.location = loc.after(s)
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
        if self._subparser.fail_ctx:
            self._subparser.fail_ctx.report(
                self.location, self._symbols, message=message, **kw)
        raise ParseBacktrackError()

    def __repr__(self):
        line, line_offs = self.location.extract_line(self._s)
        return '<speg.Parser at {!r}>'.format('{}*{}'.format(line[:line_offs], line[line_offs:]))

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
        return self._enter(track_fails=True)

    def _enter(self, track_fails):
        if track_fails and self._subparser.fail_ctx is not None:
            fail_ctx = self._subparser.fail_ctx.clone()
        else:
            fail_ctx = None

        self._subparser = _Subparser(
            self._subparser.location, fail_ctx, self._subparser)

    def __exit__(self, type, value, traceback):
        self._succeeded = type is None

        cur = self._subparser
        prev = cur.parent
        if self._succeeded:
            prev.location = cur.location
        elif cur.fail_ctx is not None:
            assert prev.fail_ctx is not None
            prev.fail_ctx.update_from(cur.fail_ctx)
        self._subparser = prev

        return type is ParseBacktrackError

    def clear(self):
        self._succeeded = True

    def __nonzero__(self):
        return self._succeeded

    __bool__ = __nonzero__

    def _symbols(self):
        cur = self._sym
        while cur is not None:
            if not getattr(cur.fn, '_speg_hidden', False):
                yield cur.fn, cur.location
            cur = cur.parent

class _Sym:
    def __init__(self, fn, location, parent):
        self.fn = fn
        self.location = location
        self.vars = None
        self.parent = parent

        if parent is None:
            self.vars_parent = None
        elif parent.vars is None:
            self.vars_parent = parent.vars_parent
        else:
            self.vars_parent = parent

class _Subparser:
    def __init__(self, location, fail_ctx, parent):
        self.location = location
        self.fail_ctx = fail_ctx
        self.parent = parent

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
            return self._p.parse(r)
        return self._p.tail[:0]

    def __enter__(self):
        return self._p._enter(track_fails=False)

    def __exit__(self, type, value, traceback):
        r = self._p.__exit__(type, value, traceback)
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
        sym = self._p._sym
        while sym is not None:
            if sym.vars and key in sym.vars:
                return sym.vars[key]
            sym = sym.vars_parent
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        sym = self._p._sym
        if sym.vars is None:
            sym.vars = { key: value }
        else:
            sym.vars[key] = value

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        sym = self._p._sym
        while sym is not None:
            if sym.vars and key in sym.vars:
                return True
            sym = sym.vars_parent
        return False

    def keys(self):
        r = set()
        sym = self._p._sym
        while sym is not None:
            if sym.vars:
                r.update(sym.vars)
            sym = sym.vars_parent
        return r

    def __len__(self):
        return len(self.keys())
