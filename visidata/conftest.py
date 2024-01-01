from unittest.mock import Mock

import pytest


def pytest_collect_file(file_path, parent):
    """Make pytest collect tests from all visidata's imported modules."""
    if file_path.suffix == ".py":
        import visidata
        modules = {
            mod.__file__
            for mod in visidata.vd.importedModules
            if hasattr(mod, "__file__")
        }
        if str(file_path) in modules:
            module = pytest.Module.from_parent(parent, path=file_path)
            module.add_marker(pytest.mark.usefixtures('curses_setup'))
            return module


@pytest.fixture(scope="class")
def curses_setup():
    """Perform some curses prepwork."""
    import curses
    import visidata

    curses.curs_set = lambda v: None
    visidata.options.overwrite = 'always'


@pytest.fixture(scope="function")
def mock_screen():
    """Set up and return a mock curses screen object."""
    scr = Mock()
    scr.addstr = lambda *args, **kwargs: None
    scr.move = lambda *args, **kwargs: None
    scr.getmaxyx = lambda: (25, 80)

    return scr


@pytest.fixture(scope="function")
def vd(mock_screen):
    """Set up and return a mock VisiData object."""
    import visidata
    visidata.vd.resetVisiData()
    visidata.vd.scr = mock_screen
    return visidata.vd
