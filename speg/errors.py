from .rules import rule_to_str

class ExpectedExpr:
    def __init__(self, text, position, callstack, expr):
        self.text = text
        self.position = position
        self.callstack = callstack
        self.expr = expr

class UnexpectedExpr:
    def __init__(self, text, position, end_pos, callstack, rule):
        self.text = text
        self.position = position
        self.end_pos = end_pos
        self.callstack = callstack
        self.rule = rule

class SemanticFailure:
    def __init__(self, text, position, callstack, args, kw):
        self.text = text
        self.position = position
        self.callstack = callstack
        self.args = args
        self.kw = kw

class ParseError(RuntimeError):
    def __init__(self, message, start_pos, end_pos, failures):
        self.message = message
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.failures = failures

    def __str__(self):
        return 'at {}:{}: {}'.format(
            self.start_pos.line, self.start_pos.col, self.message)

def _first(iterable):
    return next(iterable, None)

def raise_parsing_error(failures):
    max_pos = max(f.position for f in failures)
    end_pos = max_pos
    msg = []

    max_fails = [f for f in failures if f.position == max_pos]

    sema = _first(f for f in max_fails if isinstance(f, SemanticFailure))
    if sema is not None:
        msg.append(sema.args[0])
    else:
        unexps = [f for f in max_fails if isinstance(f, UnexpectedExpr)]
        if unexps:
            unexp = min(unexps,
                key=lambda f: f.end_pos.offset - f.position.offset)
            end_pos = unexp.end_pos
            msg.append('unexpected {}'.format(rule_to_str(unexp.rule)))

        exps = [f for f in max_fails if isinstance(f, ExpectedExpr)]
        if exps:
            exp_syms = set()
            for f in exps:
                r = _first(se.fn for se in f.callstack if se.position == max_pos)
                if r is None:
                    r = f.expr
                exp_syms.add(rule_to_str(r))
            exp_strs = sorted(exp_syms)

            if len(exp_strs) == 1:
                msg.append('expected {}'.format(exp_strs[0]))
            else:
                msg.append('expected one of {}'.format(', '.join(exp_strs)))

    raise ParseError('; '.join(msg), max_pos, end_pos, failures)
