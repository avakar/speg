class ParseBacktrackError(BaseException):
    pass

class ParseError(RuntimeError):
    def __init__(self, message, text, start_pos, end_pos):
        self.message = message
        self.location = start_pos
        self.ranges = [(start_pos, end_pos)]
        self.text = text

    def __str__(self):
        return 'at {}: {}'.format(self.location, self.message)
