from visidata import vd


def test_parsePos():
    'Test cases from PR #2425'
    inputs = [('foo.csv', {})]

    assert vd.parsePos('') is None
    assert vd.parsePos('2', inputs=inputs) == ([-1], None, '2')  # +row with inputs: last sheet
    assert vd.parsePos('2', inputs=None) == (None, None, '2')  # +row without inputs: current sheet
    assert vd.parsePos('-1', inputs=inputs) == ([-1], None, '-1')  # negative row index stays as string
    assert vd.parsePos('1:', inputs=inputs) == ([-1], 1, None)  # +col:
    assert vd.parsePos(':2', inputs=inputs) == ([-1], None, 2)  # +:row
    assert vd.parsePos('1:2', inputs=inputs) == ([-1], 1, 2)  # +col:row
    assert vd.parsePos('name:value', inputs=inputs) == ([-1], 'name', 'value')  # string col:row
    assert vd.parsePos(':1:', inputs=inputs) == ([], 1, None)  # +:col: all sheets
    assert vd.parsePos(':1:2') == ([], 1, 2)  # +:col:row all sheets
    assert vd.parsePos('::2') == ([], None, 2)  # +::row all sheets
    assert vd.parsePos('0:1:2') == ([0], 1, 2)  # +sheet:col:row
    assert vd.parsePos('1::') == ([1], None, None)  # +sheet:: switch sheet only
    assert vd.parsePos('-2::') == ([-2], None, None)  # negative sheet index
    assert vd.parsePos('0:a:1:2') == ([0, 'a'], 1, 2)  # named subsheet
    assert vd.parsePos('0:0:1:2') == ([0, 0], 1, 2)  # numeric subsheet index
    assert vd.parsePos('0:a:b:1:2') == ([0, 'a', 'b'], 1, 2)  # nested subsheets
    assert vd.parsePos(':a:1:2') == (['', 'a'], 1, 2)  # all sheets + subsheet
