from six import string_types

class Eof: pass
eof = Eof()

def rule_to_str(rule):
    if rule is eof:
        return 'eof'
    if isinstance(rule, string_types):
        return repr(rule)
    return '<{}>'.format(rule.__name__)
