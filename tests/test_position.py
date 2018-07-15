from speg.position import Position, get_line_at_position
import pytest

def test_initial():
    p = Position()
    assert p.offset == 0
    assert p.line == 1
    assert p.col == 1

def test_explicit():
    p = Position(4, 2, 2)
    assert p.offset == 4
    assert p.line == 2
    assert p.col == 2

def test_update_nonl():
    p = Position()
    q = p.advanced_by('test')

    assert p.offset == 0
    assert p.line == 1
    assert p.col == 1

    assert q.offset == 4
    assert q.line == 1
    assert q.col == 5

def test_update_nl():
    p = Position(4, 1, 5)
    q = p.advanced_by('\n')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 5
    assert q.line == 2
    assert q.col == 1

def test_update_xnl():
    p = Position(4, 1, 5)
    q = p.advanced_by('x\n')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 6
    assert q.line == 2
    assert q.col == 1

def test_update_nlx():
    p = Position(4, 1, 5)
    q = p.advanced_by('\nx')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 6
    assert q.line == 2
    assert q.col == 2

def test_update_xnlx():
    p = Position(4, 1, 5)
    q = p.advanced_by('x\nx')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 7
    assert q.line == 2
    assert q.col == 2

def test_update_xnlxnl():
    p = Position(4, 1, 5)
    q = p.advanced_by('x\nx\n')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 8
    assert q.line == 3
    assert q.col == 1

def test_update_xnlxnlx():
    p = Position(4, 1, 5)
    q = p.advanced_by('x\nx\nx')

    assert p.offset == 4
    assert p.line == 1
    assert p.col == 5

    assert q.offset == 9
    assert q.line == 3
    assert q.col == 2

def test_context_prenl():
    p = Position().advanced_by('li')
    assert get_line_at_position('line1', p) == ('line1', 2)
    assert get_line_at_position('line1\n', p) == ('line1', 2)
    assert get_line_at_position('line1\nline2', p) == ('line1', 2)
    assert get_line_at_position('line1\nline2\n', p) == ('line1', 2)

def test_context_atnl():
    p = Position().advanced_by('line1')
    assert get_line_at_position('line1', p) == ('line1', 5)
    assert get_line_at_position('line1\n', p) == ('line1', 5)
    assert get_line_at_position('line1\nline2', p) == ('line1', 5)
    assert get_line_at_position('line1\nline2\n', p) == ('line1', 5)

def test_context_postnl():
    p = Position().advanced_by('line1\n')
    assert get_line_at_position('line1\n', p) == ('', 0)
    assert get_line_at_position('line1\nline2', p) == ('line2', 0)
    assert get_line_at_position('line1\nline2\n', p) == ('line2', 0)

def test_context_postnlx():
    p = Position().advanced_by('line1\nl')
    assert get_line_at_position('line1\nline2', p) == ('line2', 1)
    assert get_line_at_position('line1\nline2\n', p) == ('line2', 1)
    assert get_line_at_position('line1\nline2\nline3', p) == ('line2', 1)
    assert get_line_at_position('line1\nline2\nline3\n', p) == ('line2', 1)

def test_eq():
    p = Position(42)
    assert p == p
    assert p == Position(42)
    assert p != 42

    assert p != Position()
    assert p != Position(41)
    assert p != Position(43)

def test_comparison():
    p = Position(42)
    assert p <= p
    assert p >= p
    assert Position(41) < p < Position(43)

    assert p.__lt__(43) is NotImplemented

def test_repr():
    p = Position(42)
    assert repr(p) == 'Position(42, 1, 1)'

def test_hash():
    assert hash(Position(1)) == hash(Position(1))
