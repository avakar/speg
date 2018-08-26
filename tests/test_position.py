# from speg import Location, get_line_at_location
# import pytest

# def test_initial():
#     p = Location()
#     assert p.index == 0
#     assert p.line == 1
#     assert p.col == 1

# def test_explicit():
#     p = Location(4, 2, 2)
#     assert p.index == 4
#     assert p.line == 2
#     assert p.col == 2

# def test_update_nonl():
#     p = Location()
#     q = p.advanced_by('test')

#     assert p.index == 0
#     assert p.line == 1
#     assert p.col == 1

#     assert q.index == 4
#     assert q.line == 1
#     assert q.col == 5

# def test_update_nl():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('\n')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 5
#     assert q.line == 2
#     assert q.col == 1

# def test_update_xnl():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('x\n')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 6
#     assert q.line == 2
#     assert q.col == 1

# def test_update_nlx():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('\nx')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 6
#     assert q.line == 2
#     assert q.col == 2

# def test_update_xnlx():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('x\nx')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 7
#     assert q.line == 2
#     assert q.col == 2

# def test_update_xnlxnl():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('x\nx\n')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 8
#     assert q.line == 3
#     assert q.col == 1

# def test_update_xnlxnlx():
#     p = Location(4, 1, 5)
#     q = p.advanced_by('x\nx\nx')

#     assert p.index == 4
#     assert p.line == 1
#     assert p.col == 5

#     assert q.index == 9
#     assert q.line == 3
#     assert q.col == 2

# def test_context_prenl():
#     p = Location().advanced_by('li')
#     assert get_line_at_position('line1', p) == ('line1', 2)
#     assert get_line_at_position('line1\n', p) == ('line1', 2)
#     assert get_line_at_position('line1\nline2', p) == ('line1', 2)
#     assert get_line_at_position('line1\nline2\n', p) == ('line1', 2)

# def test_context_atnl():
#     p = Location().advanced_by('line1')
#     assert get_line_at_position('line1', p) == ('line1', 5)
#     assert get_line_at_position('line1\n', p) == ('line1', 5)
#     assert get_line_at_position('line1\nline2', p) == ('line1', 5)
#     assert get_line_at_position('line1\nline2\n', p) == ('line1', 5)

# def test_context_postnl():
#     p = Location().advanced_by('line1\n')
#     assert get_line_at_position('line1\n', p) == ('', 0)
#     assert get_line_at_position('line1\nline2', p) == ('line2', 0)
#     assert get_line_at_position('line1\nline2\n', p) == ('line2', 0)

# def test_context_postnlx():
#     p = Location().advanced_by('line1\nl')
#     assert get_line_at_position('line1\nline2', p) == ('line2', 1)
#     assert get_line_at_position('line1\nline2\n', p) == ('line2', 1)
#     assert get_line_at_position('line1\nline2\nline3', p) == ('line2', 1)
#     assert get_line_at_position('line1\nline2\nline3\n', p) == ('line2', 1)

# def test_eq():
#     p = Location(42)
#     assert p == p
#     assert p == Location(42)
#     assert p != 42

#     assert p != Location()
#     assert p != Location(41)
#     assert p != Location(43)

# def test_comparison():
#     p = Location(42)
#     assert p <= p
#     assert p >= p
#     assert Location(41) < p < Location(43)

#     assert p.__lt__(43) is NotImplemented

# def test_repr():
#     p = Location(42)
#     assert repr(p) == 'Location(42, 1, 1)'

# def test_hash():
#     assert hash(Location(1)) == hash(Location(1))
