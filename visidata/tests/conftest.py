import pytest
from unittest.mock import Mock


@pytest.fixture(scope="class")
def curses_setup():
    """Perform some curses prepwork"""

    import curses
    import visidata

    curses.curs_set = lambda v: None
    visidata.options.confirm_overwrite = False


@pytest.fixture(scope="function")
def mock_screen():
    """Set up and return a mock curses screen object."""

    scr = Mock()
    scr.addstr = Mock()
    scr.move = Mock()
    scr.getmaxyx = lambda: (25, 80)

    return scr
