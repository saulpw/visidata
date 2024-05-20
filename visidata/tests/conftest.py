import pytest
from unittest.mock import Mock


@pytest.fixture(scope="class")
def curses_setup():
    """Perform some curses prepwork"""

    import curses
    import visidata

    curses.curs_set = lambda v: None
    curses.doupdate = lambda: None
    visidata.options.overwrite = 'always'


@pytest.fixture(scope="function")
def mock_screen():
    """Set up and return a mock curses screen object."""

    scr = Mock()
    scr.addstr = lambda *args, **kwargs: None
    scr.move = lambda *args, **kwargs: None
    scr.getmaxyx = lambda: (25, 80)

    return scr
