from unittest.mock import Mock

import pytest

from visidata import vd, ColorAttr, InputWidget
from visidata.features.history_palette import HistoryPalette


@pytest.mark.parametrize('default, keys, expected', [
    ('benchmark.csv', 'Up Enter', 'zzz.json'),
    ('benchmark.csv', 'Up Down Enter', 'benchmark.csv'),
    ('benchmark.csv', 'End Ctrl+U Up Enter', 'benchmark.csv'),
    ('benchmark.csv', 'End Ctrl+U Up Up Enter', 'zzz.json'),
    ('benchmark.csv', 'End Ctrl+U Up Down Enter', ''),
    ('benchmark.csv', 'x Up Enter', 'benchmark.csv'),
    ('benchmark.csv', 'x Up Down Enter', 'x'),
    ('benchmark.csv', 'f Up Up Enter', 'foo.tsv'),
    ('', 'Up Enter', 'zzz.json'),
    ('', 'Up Down Enter', ''),
])
def test_history_palette_default(mock_screen, monkeypatch, default, keys, expected):
    items = ['out1.csv', 'foo.tsv', 'zzz.json']
    pal = HistoryPalette(Mock(windowHeight=25, _scr=None), items, 1, lambda v: None, default=default)
    monkeypatch.setattr(vd, 'getkeystroke', Mock(side_effect=keys.split()))
    widget = InputWidget(value=default, history=items)

    result = widget.editline(mock_screen, 0, 0, 0, attr=ColorAttr(), updater=pal.draw,
                             bindings=dict(Up=pal.nav_up, Down=pal.nav_down, End=pal.nav_end))

    assert result == expected
