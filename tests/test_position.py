from speg import BasicLocation, Location
import pytest

def test_basic_empty():
    p = BasicLocation()
    assert p.index == 0
    assert str(p) == 'offset 0'
    assert repr(p) == 'BasicLocation(0)'

def test_basic_init():
    p = BasicLocation(10)
    assert p.index == 10

def test_basic_readonly_index():
    p = BasicLocation(10)
    with pytest.raises(AttributeError):
        p.index = 11

def test_basic_update():
    p = BasicLocation(10)

    p2 = p.after('text')
    assert p2.index == 14

    p3 = p.after('')
    assert p3.index == 10

def test_basic_compare():
    assert BasicLocation() == BasicLocation()
    assert BasicLocation() == BasicLocation(0)
    assert BasicLocation() != BasicLocation(1)
    assert BasicLocation() < BasicLocation(1)

def test_basic_extract():
    p0 = BasicLocation(0)
    assert p0.extract_line_range('') == (0, 0)
    assert p0.extract_line('') == ('', 0)

    p5 = BasicLocation(5)
    assert p5.extract_line_range('123\n5678') == (4, 8)
    assert p5.extract_line_range('1234\n678') == (5, 8)
    assert p5.extract_line_range('12345\n78') == (0, 5)
    assert p5.extract_line_range('123456\n8') == (0, 6)
    assert p5.extract_line_range('1234567\n') == (0, 7)
    assert p5.extract_line_range('12345678') == (0, 8)
    assert p5.extract_line_range('\n23\n5678') == (4, 8)
    assert p5.extract_line_range('\n234\n678') == (5, 8)
    assert p5.extract_line_range('\n2345\n78') == (1, 5)
    assert p5.extract_line_range('\n23456\n8') == (1, 6)
    assert p5.extract_line_range('\n234567\n') == (1, 7)
    assert p5.extract_line_range('\n2345678') == (1, 8)
    assert p5.extract_line_range('\n\n\n\n\n\n\n\n') == (5, 5)

    assert p5.extract_line('123\n5678') == ('5678', 1)
    assert p5.extract_line('1234\n678') == ('678', 0)
    assert p5.extract_line('12345\n78') == ('12345', 5)
    assert p5.extract_line('123456\n8') == ('123456', 5)
    assert p5.extract_line('1234567\n') == ('1234567', 5)
    assert p5.extract_line('12345678') == ('12345678', 5)
    assert p5.extract_line('\n23\n5678') == ('5678', 1)
    assert p5.extract_line('\n234\n678') == ('678', 0)
    assert p5.extract_line('\n2345\n78') == ('2345', 4)
    assert p5.extract_line('\n23456\n8') == ('23456', 4)
    assert p5.extract_line('\n234567\n') == ('234567', 4)
    assert p5.extract_line('\n2345678') == ('2345678', 4)
    assert p5.extract_line('\n\n\n\n\n\n\n\n') == ('', 0)

def test_empty():
    p = Location()
    assert p.index == 0
    assert p.nl_count == 0
    assert p.nl_index == -1
    assert str(p) == '1:1'
    assert repr(p) == 'Location(0, nl_count=0, nl_index=-1)'

def test_init():
    p = Location(5)
    assert p.index == 5
    assert p.nl_count == 0
    assert p.nl_index == -1
    assert str(p) == '1:6'
    assert repr(p) == 'Location(5, nl_count=0, nl_index=-1)'

def test_init_with_line():
    p = Location(5, nl_count=2, nl_index=3)
    assert p.index == 5
    assert p.nl_count == 2
    assert p.nl_index == 3
    assert str(p) == '3:2'
    assert repr(p) == 'Location(5, nl_count=2, nl_index=3)'

def test_update_nonl():
    p = Location(4)
    assert p.index == 4
    assert p.nl_count == 0
    assert p.nl_index == -1

    q = p.after('x')
    assert q.index == 5
    assert q.nl_count == 0
    assert q.nl_index == -1

def test_update_nl():
    p = Location(4).after('\n')
    assert p.index == 5
    assert p.nl_count == 1
    assert p.nl_index == 4

def test_update_xnl():
    p = Location(4).after('x\n')
    assert p.index == 6
    assert p.nl_count == 1
    assert p.nl_index == 5

def test_update_nlx():
    p = Location(4).after('\nx')
    assert p.index == 6
    assert p.nl_count == 1
    assert p.nl_index == 4

def test_update_xnlx():
    p = Location(4).after('x\nx')
    assert p.index == 7
    assert p.nl_count == 1
    assert p.nl_index == 5

def test_update_xnlxnl():
    p = Location(4).after('x\nx\n')
    assert p.index == 8
    assert p.nl_count == 2
    assert p.nl_index == 7

def test_update_xnlxnlx():
    p = Location(4).after('x\nx\nx')
    assert p.index == 9
    assert p.nl_count == 2
    assert p.nl_index == 7

def test_extract_prenl():
    p = Location().after('li')
    assert p.extract_line('line1') == ('line1', 2)
    assert p.extract_line('line1\n') == ('line1', 2)
    assert p.extract_line('line1\nline2') == ('line1', 2)
    assert p.extract_line('line1\nline2\n') == ('line1', 2)

def test_extract_atnl():
    p = Location().after('line1')
    assert p.extract_line('line1') == ('line1', 5)
    assert p.extract_line('line1\n') == ('line1', 5)
    assert p.extract_line('line1\nline2') == ('line1', 5)
    assert p.extract_line('line1\nline2\n') == ('line1', 5)

def test_extract_postnl():
    p = Location().after('line1\n')
    assert p.extract_line('line1\n') == ('', 0)
    assert p.extract_line('line1\nline2') == ('line2', 0)
    assert p.extract_line('line1\nline2\n') == ('line2', 0)

def test_extract_postnlx():
    p = Location().after('line1\nl')
    assert p.extract_line('line1\nline2') == ('line2', 1)
    assert p.extract_line('line1\nline2\n') == ('line2', 1)
    assert p.extract_line('line1\nline2\nline3') == ('line2', 1)
    assert p.extract_line('line1\nline2\nline3\n') == ('line2', 1)

def test_eq():
    p = Location(42)
    assert p == p
    assert p == Location(42)
    assert p != 42

    assert p != Location()
    assert p != Location(41)
    assert p != Location(43)

def test_comparison():
    p = Location(42)
    assert p <= p
    assert p >= p
    assert Location(41) < p < Location(43)

    assert p.__lt__(43) is NotImplemented

def test_hash():
    assert hash(Location(1)) == hash(Location(1))
