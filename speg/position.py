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

def get_line_at_position(text, pos):
    suffix = text[pos.index - pos.col + 1:]
    stop = suffix.find('\n')
    if stop == -1:
        return suffix, pos.col - 1
    else:
        return suffix[:stop], pos.col - 1
