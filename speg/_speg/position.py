from functools import total_ordering

@total_ordering
class Location(object):
    def __init__(self, index=0, line=1, col=1):
        self.index = index
        self.line = line
        self.col = col

    def advanced_by(self, text):
        text_len = len(text)
        index = self.index + text_len
        nl_pos = text.rfind('\n')
        if nl_pos < 0:
            line = self.line
            col = self.col + text_len
        else:
            line = self.line + text[:nl_pos].count('\n') + 1
            col = text_len - nl_pos
        return Location(index, line, col)

    def __eq__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        return self.index == other.index

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.index)

    def __lt__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        return self.index < other.index

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(Location.__name__,
            self.index, self.line, self.col)

def get_line_range_by_location(text, location):
    start = Location(location.index - location.col + 1, location.line, 1)
    end_idx = text.find('\n', start.index)
    if end_idx == -1:
        return start, Location(len(text), location.line, len(text) - start.index + 1)
    else:
        return start, Location(end_idx, location.line, end_idx - start.index + 1)

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

def count_cols(s):
    for ch in s

def format_ranges(text, center, ranges):
    line_start, line_end = get_line_range_by_location(text, center)
    assert line_start.line == line_end.line

    line_text = text[line_start.index:line_end.index]
    idx_ranges = get_index_ranges_for_line(line_start.line, line_end.index - line_start.index, ranges)

    r = [line_text, '\n']

    last_idx = 0
    for start_idx, end_idx in idx_ranges:
