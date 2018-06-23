class ParseError(Exception):
    pass

class ExpectedExprError(ParseError):
    def __init__(self, text, position, callstack, expr):
        self.text = text
        self.position = position
        self.callstack = callstack
        self.expr = expr
        super(ExpectedExprError, self).__init__(text)

class UnexpectedExprError(ParseError):
    def __init__(self, text, start_pos, end_pos, callstack, rule):
        self.text = text
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.callstack = callstack
        self.rule = rule
        super(UnexpectedExprError, self).__init__(text)

class SemanticError(ParseError):
    def __init__(self, text, position, callstack, args, kw):
        self.text = text
        self.position = position
        self.callstack = callstack
        self.args = args
        self.kw = kw
        super(SemanticError, self).__init__(text)
