class ParseBacktrackError(BaseException):
    pass

class Diagnostic:
    def __init__(self, message, location, ranges):
        self.message = message
        self.location = location
        self.ranges = frozenset(ranges)

class ParseError(RuntimeError):
    def __init__(self, diagnostics, text):
        self.diagnostics = tuple(diagnostics)
        self.text = text

    def __str__(self):
        diag = self.diagnostics[0]
        return 'at {}: {}'.format(diag.location, diag.message)
