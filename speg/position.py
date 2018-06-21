class Position:
    def __init__(self, offset, line, col):
        self.offset = offset
        self.line = line
        self.col = col

    @staticmethod
    def initial():
        return Position(0, 1, 1)

    def update(self, text):
        text_len = len(text)
        offset = self.offset + text_len
        nl_pos = text.rfind('\n')
        if nl_pos < 0:
            line = self.line
            col = self.col + text_len
        else:
            line = self.line + text[:nl_pos].count('\n') + 1
            col = text_len - nl_pos
        return Position(offset, line, col)
