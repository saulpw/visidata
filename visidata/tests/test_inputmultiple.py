from unittest.mock import Mock

import visidata


def _bindingsByPrompt(monkeypatch, **fields):
    'Run inputMultiple with *fields*; return the bindings vd.input got for each prompt.'
    sheet = Mock(_scr=None, windowWidth=80, windowHeight=25)
    monkeypatch.setattr(type(visidata.vd), 'activeSheet', property(lambda vd: sheet))
    monkeypatch.setattr(visidata.vd, 'getCommandInput', lambda: None)

    got = {}
    def _input(prompt='', bindings={}, **kwargs):
        got[prompt] = bindings
        return ''
    monkeypatch.setattr(visidata.vd, 'input', _input)

    visidata.vd.inputMultiple(record=False, **fields)
    return got


def test_tab_completes_in_field_with_completer(monkeypatch):  #3169
    got = _bindingsByPrompt(monkeypatch,
                            path=dict(prompt='open: ', completer=lambda v, i: None),
                            filetype=dict(prompt='as filetype: '))
    assert 'Tab' not in got['open: ']
    assert 'Shift+Tab' not in got['open: ']
    assert 'Shift+Down' in got['open: ']


def test_tab_switches_field_without_completer(monkeypatch):
    got = _bindingsByPrompt(monkeypatch, regex=dict(prompt='regex: '), flags=dict(prompt='flags: '))
    assert 'Tab' in got['regex: ']
    assert 'Shift+Tab' in got['regex: ']
