class ParseBacktrackError(BaseException):
    pass

class ParseError(RuntimeError):
    def __init__(self, message, text, start_pos, end_pos):
        self.message = message
        self.location = start_pos
        self.ranges = [(start_pos, end_pos)]
        self.text = text

    def __str__(self):
        return 'at {}:{}: {}'.format(
            self.location.line, self.location.line_index + 1, self.message)

    def format_message(self, filename='<input>'):
        r = ['{}:{}:{}: error: {}\n'.format(
            filename, self.location.line, self.location.line_index + 1, self.message)]
        return ''.join(r)
