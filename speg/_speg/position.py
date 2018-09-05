from functools import total_ordering

@total_ordering
class BasicLocation(object):
    def __init__(self, index=0):
        self._index = index

    @property
    def index(self):
        return self._index

    def after(self, text):
        return BasicLocation(self._index + len(text))

    def extract_line_range(self, text):
        start_idx = text.rfind('\n', 0, self._index)
        if start_idx == -1:
            start_idx = 0
        end_idx = text.find('\n', self._index)
        if end_idx == -1:
            end_idx = len(text)
        return start_idx, end_idx

    def extract_line(self, text):
        start_idx, end_idx = self.extract_line_range(text)
        assert start_idx <= self._index < end_idx
        return text[start_idx:end_idx], self._index - start_idx

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

    def __str__(self):
        return 'offset {}'.format(self._index)

    def __repr__(self):
        return 'BasicLocation({!r})'.format(self._index)

class Location(BasicLocation):
    def __init__(self, index=0, nl_count=0, nl_index=-1):
        super(Location, self).__init__(index)
        self.nl_count = nl_count
        self.nl_index = nl_index

    def after(self, text):
        text_len = len(text)
        index = self.index
        pos = text.rfind('\n')
        if pos < 0:
            return Location(index + text_len, self.nl_count, self.nl_index)

        return Location(
            index + text_len,
            self.nl_count + text[:pos].count('\n') + 1,
            index + pos)

    def __str__(self):
        return '{}:{}'.format(self.nl_count + 1, self.index - self.nl_index)

    def __repr__(self):
        return 'Location({!r}, nl_count={!r}, nl_index={!r})'.format(
            self.index, self.nl_count, self.nl_index)

    def extract_line_range(self, text):
        start_idx = self.nl_index + 1
        end_idx = text.find('\n', start_idx)
        if end_idx == -1:
            end_idx = len(text)
        return start_idx, end_idx

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
