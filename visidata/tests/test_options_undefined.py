import pytest

from visidata import vd, Sheet, Path


def warnings(name=None):
    'Count warnings about unknown options, optionally for one message.'
    return sum(r[2] for r in vd.statusHistory
               if r[0] == 1 and 'unknown option' in str(r[1])
               and (name is None or r[1] == (name,)))


@pytest.fixture(autouse=True)
def fresh():
    vd.statusHistory.clear()
    getattr(type(vd.options), '_warned_unknown_options', set()).clear()
    yield
    vd.statusHistory.clear()
    getattr(type(vd.options), '_warned_unknown_options', set()).clear()


def test_numeric_formatter_without_type_fmt():
    assert vd.numericFormatter('', True) == 'True'
    assert vd.numericFormatter('', {'a': 1}) == "{'a': 1}"
    assert vd.numericFormatter('', [1, 2]) == '[1, 2]'
    assert vd.numericFormatter('', 42) == '42'
    assert vd.numericFormatter('', 1.25) == '1.25'
    assert vd.numericFormatter('{:04d}', 42) == '0042'
    assert warnings() == 0


def test_get_with_default_is_silent():
    assert vd.options.get('issue2861_attr', 'fallback') == 'fallback'
    assert vd.options.get('issue2861_item') is None
    assert warnings() == 0


def test_undefined_read_returns_none_and_warns_once():
    assert vd.options.issue2861_attr is None
    assert vd.options['issue2861_item'] is None
    assert vd.options.getonly('issue2861_only', 'global', 'fallback') is None

    # again, through other contexts: no more warnings
    sheet = Sheet('issue2861')
    assert sheet.options.issue2861_attr is None
    assert Sheet('issue2861_other').options['issue2861_attr'] is None
    assert Path('issue2861.tsv').options.issue2861_item is None
    assert vd.options.getonly('issue2861_attr', sheet, 'fallback') is None
    assert vd.options.issue2861_only is None

    assert warnings('reading unknown option `issue2861_attr`') == 1
    assert warnings('reading unknown option `issue2861_item`') == 1
    assert warnings('reading unknown option `issue2861_only`') == 1
    assert warnings() == 3

    # clearing caches does not repeat the warning
    vd.options._cache.clear()
    vd.clearCaches()
    assert vd.options['issue2861_attr'] is None
    assert warnings() == 3


def test_late_declaration():
    assert vd.options.issue2861_late is None
    vd.option('issue2861_late', 17, 'test late option declaration')
    sheet = Sheet('issue2861')
    assert vd.options.issue2861_late == 17
    assert sheet.options['issue2861_late'] == 17
    assert vd.options.getonly('issue2861_late', sheet, 'fallback') == 'fallback'
    sheet.options.issue2861_late = 23
    assert sheet.options.issue2861_late == 23
    assert vd.options.getonly('issue2861_late', sheet, 'fallback') == 23


def test_defined_falsy_options_do_not_warn():
    vd.option('issue2861_none', None, 'test defined null option')
    vd.option('issue2861_false', False, 'test defined false option')
    assert vd.options.issue2861_none is None
    assert vd.options['issue2861_none'] is None
    assert vd.options.get('issue2861_none', 'fallback') is None
    assert vd.options.getonly('issue2861_none', 'default', 'fallback') is None
    assert vd.options.issue2861_false is False
    assert vd.options['issue2861_false'] is False
    assert vd.options.getonly('issue2861_false', 'default', 'fallback') is False
    assert warnings() == 0


def test_setting_unknown_option_still_warns():
    vd.options.set('issue2861_set', 42, cmdlog=False)
    assert vd.options.issue2861_set == 42
    assert warnings('setting unknown option `issue2861_set`') == 1


def test_private_attrs_are_not_options():
    assert not hasattr(vd.options, '__deepcopy__')
    assert not hasattr(vd.options, '_repr_html_')
    with pytest.raises(AttributeError):
        vd.options._issue2861_private
    assert warnings() == 0
