from .position import Location

class ParseError(RuntimeError):
    def __init__(self, message, text, start_pos, end_pos):
        self.message = message
        self.location = start_pos
        self.ranges = [(start_pos, end_pos)]
        self.text = text

    def __str__(self):
        return 'at {}:{}: {}'.format(
            self.location.line, self.location.col, self.message)

    def format_message(self, filename='<input>'):
        r = ['{}:{}:{}: error: {}\n'.format(
            filename, self.location.line, self.location.col, self.message)]
        return ''.join(r)

class _Symbol:
    def __init__(self, parent, parent_height, location, fn, args, kw):
        self.parent = parent
        self.parent_height = parent_height
        self.location = location
        self.fn = fn
        self.args = args
        self.kw = kw

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

class FailHandler:
    def __init__(self, initial_location):
        self._symbol = None
        self._symbol_height = 0
        self._state_stack = [_FailState(initial_location)]
        self._suppress = 0

    def push_symbol(self, location, fn, args, kw):
        if self._suppress:
            return

        if not getattr(fn, '_speg_hidden', False) and (self._symbol is None or self._symbol.location < location):
            self._symbol = _Symbol(self._symbol, self._symbol_height, location, fn, args, kw)
            self._symbol_height = 0
        else:
            self._symbol_height += 1

    def pop_symbol(self):
        if self._suppress:
            return

        if self._symbol_height:
            self._symbol_height -= 1
        else:
            self._symbol_height = self._symbol.parent_height
            self._symbol = self._symbol.parent

    def push_suppress(self):
        self._suppress += 1

    def pop_suppress(self):
        self._suppress -= 1

    def push_state(self, location):
        if self._suppress:
            return
        self._state_stack.append(_FailState(location))

    def pop_state(self, succeeded):
        if self._suppress:
            return

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
        assert not self._suppress
        assert len(self._state_stack) == 1
        st = self._state_stack[0]
        end_loc = st.location

        msg = []
        for sema in st.sema:
            msg.extend(str(x) for x in sema)

        if st.unexpected is not None:
            msg.append('unexpected {}'.format(st.unexpected))
            end_loc = st.unexpected_end_loc

        if st.expected:
            if len(st.expected) == 1:
                msg.append('expected {}'.format(next(iter(st.expected))))
            else:
                msg.append('expected one of {}'.format(', '.join(st.expected)))

        if not msg:
            msg.append('failed')

        return ParseError('; '.join(msg), text, st.location, end_loc)

    def expected_eof(self, location):
        if self._update_location(location):
            self._state_stack[-1].expected.add(self._get_symbol('eof'))

    def expected_string(self, location, s):
        if self._update_location(location):
            self._state_stack[-1].expected.add(self._get_symbol(repr(s)))

    def expected_match(self, location, pattern):
        if self._update_location(location):
            self._state_stack[-1].expected.add(self._get_symbol(repr(pattern)))

    def unexpected_symbol(self, start_loc, end_loc, fn):
        if self._update_location(start_loc):
            st = self._state_stack[-1]
            if st.unexpected is None or st.unexpected_end_loc > end_loc:
                st.unexpected = _get_fn_name(fn)
                st.unexpected_end_loc = end_loc

    def explicit_fail(self, location, args, kw):
        if self._update_location(location):
            self._state_stack[-1].sema.append(args)

    def _update_location(self, location):
        if self._suppress:
            return False

        st = self._state_stack[-1]
        if st.location > location:
            return False

        if st.location < location:
            st.location = location
            st.expected.clear()
            del st.sema[:]
        return True

    def _get_symbol(self, default):
        if not self._symbol or self._symbol.location != self._state_stack[-1].location:
            return default
        return _get_fn_name(self._symbol.fn)
