from functools import total_ordering

@total_ordering
class Location(object):
    def __init__(self, index=0, line=1, line_index=0):
        self._index = index
        self._line = line
        self._line_index = line_index

    @property
    def index(self):
        return self._index

    @property
    def line(self):
        return self._line

    @property
    def line_index(self):
        return self._line_index

    def after(self, text):
        text_len = len(text)
        index = self._index + text_len
        nl_pos = text.rfind('\n')
        if nl_pos < 0:
            line = self._line
            line_index = self._line_index + text_len
        else:
            line = self._line + text[:nl_pos].count('\n')
            line_index = text_len - nl_pos
        return Location(index, line, line_index)

    def __eq__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        return self._index == other._index

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self._index)

    def __lt__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        return self._index < other._index

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(Location.__name__,
            self._index, self._line, self._line_index)

def get_line_range_by_location(text, location):
    start = Location(location.index - location.line_index, location.line, 0)
    end_idx = text.find('\n', start.index)
    if end_idx == -1:
        return start, Location(len(text), location.line, len(text) - start.index)
    else:
        return start, Location(end_idx, location.line, end_idx - start.index)

def get_line_at_location(text, loc):
    start, stop = get_line_range_by_location(text, loc)
    assert start.index <= loc.index < stop.index
    return text[start.index:stop.index], loc.index - start.index

def get_index_ranges_for_line(lineno, linelen, ranges):
    idx_ranges = []
    for range_start, range_end in ranges:
        if range_start.line > lineno or range_end.line < lineno:
            continue

        start_idx = 0 if range_start.line < lineno else range_start.col
        end_idx = linelen if range_end.line > lineno else range_end.col

        if start_idx != end_idx:
            idx_ranges.append((start_idx, end_idx))

    if not idx_ranges:
        return idx_ranges

    idx_ranges.sort()

    r = []

    cur_start, cur_end = idx_ranges[0]
    for col_start, col_end in idx_ranges[1:]:
        if col_start <= cur_end:
            cur_end = max(cur_end, col_end)
        else:
            r.append((cur_start, cur_end))
            cur_start, cur_end = col_start, col_end

    r.append((cur_start, cur_end))
    return r
