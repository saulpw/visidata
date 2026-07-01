import pytest
from visidata import vd, Sheet, BaseSheet


def accumulate_keystrokes(keys):
    '''Simulate mainloop keystroke accumulation (mainloop.py:214-252).
    Returns (outcome, keystrokes) where outcome is one of:
      "execute", "prefix", "duplicate", "no-command".
    '''
    vd.keystrokes = ''
    prefixWaiting = False

    for key in keys:
        if not prefixWaiting:
            vd.keystrokes = ''

        keystroke = vd.prettykeys(key)
        potential = vd.keystrokes + keystroke
        if keystroke and keystroke in vd.allPrefixes and keystroke in vd.keystrokes and potential not in vd.allPrefixes and vd.bindkeys._get(potential) is None:
            vd.keystrokes = ''
            return ('duplicate', keystroke)
        else:
            vd.keystrokes = potential

        if vd.bindkeys._get(vd.keystrokes) is not None:
            return ('execute', vd.keystrokes)
        elif vd.keystrokes in vd.allPrefixes:
            prefixWaiting = True
        else:
            return ('no-command', vd.keystrokes)

    return ('prefix', vd.keystrokes)


@pytest.fixture(autouse=True)
def setup_custom_prefixes():
    orig_prefixes = vd.allPrefixes[:]
    vd.allPrefixes += ['s', 'sb']
    Sheet.unbindkey('s')
    BaseSheet.addCommand('sbk', 'test-sbk', 'pass')
    BaseSheet.addCommand('sbs', 'test-sbs', 'pass')
    vs = Sheet('test_keystrokes')
    vd.sheets = [vs]
    yield
    vd.allPrefixes[:] = orig_prefixes
    vd.sheets.clear()


@pytest.mark.parametrize('keys, expected_outcome, expected_keystrokes', [
    # built-in prefixed commands
    (['z', 'z'], 'execute', 'zz'),
    (['g', 'g'], 'execute', 'gg'),

    # custom multi-prefix commands  #3012
    (['s', 'b', 'k'], 'execute', 'sbk'),
    (['s', 'b', 's'], 'execute', 'sbs'),

    # duplicate prefix detection
    (['g', 'z', 'g'], 'duplicate', 'g'),

    # unbound sequences with repeated prefix
    (['g', 'z', 'z'], 'duplicate', 'z'),
])
def test_prefix_keystrokes(keys, expected_outcome, expected_keystrokes):
    outcome, keystrokes = accumulate_keystrokes(keys)
    assert outcome == expected_outcome
    assert keystrokes == expected_keystrokes
