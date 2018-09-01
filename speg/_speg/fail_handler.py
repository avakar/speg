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

class _FailState:
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

    def report(self, current_symbol, message=None, expected=None, unexpected=None):
        if expected is not None:
            self.expected.add(current_symbol or expected)
        if unexpected is not None:
            end_loc, fn = unexpected
            if self.unexpected is None or self.unexpected_end_loc > end_loc:
                self.unexpected = _get_fn_name(fn)
                self.unexpected_end_loc = end_loc
        if message is not None:
            self.sema.append(message)

class FailHandler:
    def __init__(self, initial_location):
        self._symbol = None
        self._symbol_height = 0
        self._state_stack = [_FailState(initial_location)]

    def push_symbol(self, location, fn):
        if not getattr(fn, '_speg_hidden', False) and (self._symbol is None or self._symbol.location < location):
            self._symbol = _Symbol(self._symbol, self._symbol_height, location, fn)
            self._symbol_height = 0
        else:
            self._symbol_height += 1

    def pop_symbol(self):
        if self._symbol_height:
            self._symbol_height -= 1
        else:
            self._symbol_height = self._symbol.parent_height
            self._symbol = self._symbol.parent

    def push_state(self, location):
        self._state_stack.append(_FailState(location))

    def pop_state(self, succeeded):
        if not succeeded:
            cur = self._state_stack[-1]
            prev = self._state_stack[-2]

            assert prev.location <= cur.location
            if prev.location == cur.location:
                prev.update(cur)
            else:
                self._state_stack[-2] = cur

        self._state_stack.pop()

    def parse_error(self, text):
        assert len(self._state_stack) == 1
        st = self._state_stack[0]
        end_loc = st.location

        msg = []
        for sema in st.sema:
            msg.extend(str(x) for x in sema)

        if st.unexpected is not None:
            msg.append('unexpected {}'.format(st.unexpected))
            end_loc = st.unexpected_end_loc

        exp = sorted(st.expected)
        if len(exp) == 1:
            msg.append('expected {}'.format(exp[0]))
        elif len(exp) > 1:
            msg.append('expected {} or {}'.format(', '.join(exp[:-1]), exp[-1]))

        if not msg:
            msg.append('failed')

        return ParseError('; '.join(msg), text, st.location, end_loc)

    def report(self, location, symbol_stack, **kw):
        for sym in symbol_stack:
            print(sym)

        st = self._state_stack[-1]
        if st.location > location:
            return False

        if st.location < location:
            st.location = location
            st.expected.clear()
            del st.sema[:]

        current_symbol = None
        if self._symbol and self._symbol.location == self._state_stack[-1].location:
            current_symbol = _get_fn_name(self._symbol.fn)

        st.report(current_symbol, **kw)
