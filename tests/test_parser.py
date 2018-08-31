from speg import parse, ParseError, hidden
import pytest

# def test_simple():
#     with parser('') as p:
#         p.eat('')

#     with parser('test') as p:
#         p.eat('')

#     with parser('test') as p:
#         p.eat('t')

#     with parser('test') as p:
#         p.eat('te')

# def test_position():
#     with parser("line1\nline2\n") as p:
#         pp = p.location
#         assert pp.index == 0
#         assert pp.line == 1
#         assert pp.col == 1

#         p.eat("li")
#         pp = p.location
#         assert pp.index == 2
#         assert pp.line == 1
#         assert pp.col == 3

#         p.eat('ne1\nl')
#         pp = p.location
#         assert pp.index == 7
#         assert pp.line == 2
#         assert pp.col == 2

# def test_rule():
#     def rule(p):
#         return p.re(r'..'), p.re(r'..')

#     with parser('test') as p:
#         n = p(rule)
#         assert n == ('te', 'st')

# def test_re():
#     with parser("3141569") as p:
#         n = p.re(r'[123]*')
#         assert n == '31'
#         assert p.index == 2

# def test_simple_fail():
#     with pytest.raises(ParseError):
#         with parser('') as p:
#             p.eat('t')

# def test_simple_rule():
#     def root(p):
#         return 2 * p.re('.')
#     with parser("test") as p:
#         assert p(root) == 'tt'

# def test_eof():
#     with parser('') as p:
#         p.check_eof()

# def test_failed_eof():
#     try:
#         with parser("xx") as p:
#             p.check_eof()
#             assert False
#     except ParseError as e:
#         assert e.message == 'expected end of input'
#         assert e.start_pos.index == 0
#         assert e.end_pos.index == 0

#     try:
#         with parser("xx") as p:
#             p.eat('x')
#             p.check_eof()
#             assert False
#     except ParseError as e:
#         assert e.message == 'expected end of input'
#         assert e.start_pos.index == 1
#         assert e.end_pos.index == 1

# def test_parser():
#     with parser("text") as p:
#         assert p.eat("") == ""
#         assert p.eat("te") == "te"
#         assert p.re(r'..') == "xt"

# def test_error():
#     def root(p):
#         p.eat('te')
#         p.eat('xx')

#     try:
#         parse("test", root)
#         assert False
#     except ParseError as e:
#         assert e.start_pos.index == 2
#         assert e.end_pos.index == 2

# def test_sema_error():
#     def root(p):
#         p.eat('te')
#         p.fail()

#     with pytest.raises(ParseError):
#         parse("test", root)

# def test_not():
#     def ident_char(p):
#         p.re('[0-9]')

#     def ident(p):
#         p.not_(ident_char)
#         return p.re('[_a-zA-Z0-9]+')

#     def num(p):
#         r = p.re(r'[0-9]+')
#         p.not_(ident)
#         return int(r, 10)

#     assert parse('123', num) == 123

#     try:
#         parse('123a', num)
#         assert False
#     except ParseError as e:
#         assert e.message == 'unexpected <ident>'
#         assert e.start_pos.index == 3
#         assert e.end_pos.index == 4

# def test_error_priority():
#     def root(p):
#         with p:
#             return p(num)
#         return p(undef)

#     def num(p):
#         r = p.re(r'[0-9]+')
#         p.eat('s')
#         return int(r, 10)

#     def undef(p):
#         p.eat('x')

#     try:
#         parse("t", root)
#         assert False
#     except ParseError as e:
#         assert e.start_pos.index == 0

#     try:
#         parse("1", root)
#         assert False
#     except ParseError as e:
#         assert e.start_pos.index == 1

# def test_repr():
#     with parser('test') as p:
#         assert repr(p) == "<speg.ParsingState at '*test'>"
#         p.eat('te')
#         assert repr(p) == "<speg.ParsingState at 'te*st'>"

# def test_multiple_exp_fails():
#     def operator(p):
#         return p.re(r'[+\-]')

#     def atom_expr(p):
#         with p:
#             p.eat('(')
#             r = p(bin_expr)
#             p.eat(')')
#             return r

#         return int(p.re(r'[0-9]+'), 10)

#     def bin_expr(p):
#         r = p(atom_expr)

#         while p:
#             with p:
#                 op = p(operator)
#                 rhs = p(atom_expr)

#                 if op == '+':
#                     r += rhs
#                 elif op == '-':
#                     r -= rhs

#         return r

#     def root(p):
#         r = p(bin_expr)
#         p.check_eof()
#         return r

#     assert parse('1', root) == 1
#     assert parse('1+1', root) == 2
#     assert parse('1+(2+3)', root) == 6
#     assert parse('1+(2-3)', root) == 0
#     assert parse('1-(2+3)', root) == -4
#     assert parse('1-2+3', root) == 2

#     try:
#         with parser('1+') as p:
#             p(root)
#         assert False
#     except ParseError as e:
#         assert str(e) == 'at 1:3: expected <atom expr>'

# def test_hidden_rule():
#     def x(p):
#         p.eat('x')

#     @hidden
#     def root(p):
#         p(x)
#         p.check_eof()

#     try:
#         parse('y', root)
#     except ParseError as e:
#         assert str(e) == 'at 1:1: expected <x>'

# def test_named_rule():
#     def x(p):
#         """whizzing frobulator"""
#         p.eat('x')

#     @hidden
#     def root(p):
#         p(x)
#         p.check_eof()

#     try:
#         parse('y', root)
#     except ParseError as e:
#         assert str(e) == 'at 1:1: expected whizzing frobulator'

# def test_opt():
#     def ws(p):
#         p.re(r' +')

#     def x(p):
#         p.eat('x')

#     @hidden
#     def root(p):
#         p.opt(ws)
#         p(x)

#     parse('  x', root)
#     parse('x', root)

#     try:
#         parse('y', root)
#         assert False
#     except ParseError as e:
#         assert e.message == 'expected <x>'

# def test_opt_context():
#     with parser('xyz') as p:
#         assert p.index == 0
#         p.eat('x')
#         assert p.index == 1
#         with p.opt:
#             assert p.index == 1
#             p.eat('y')
#             assert p.index == 2
#             p.eat('a')
#         assert p
#         assert p.index == 1
#         p.eat('y')
#         assert p.index == 2
