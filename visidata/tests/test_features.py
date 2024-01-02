import pytest
import visidata

def pytest_generate_tests(metafunc):
    """Split feature tests into separate test cases

    Look up test methods in imported modules. Turn each one into a single test_feature()
    case, with "module::method" as the test id.
    """
    tests = [
        (mod, getattr(mod, k))
        for mod in visidata.vd.importedModules
        for k in dir(mod)
        if k.startswith("test_")
    ]
    argvalues = [[testfunc] for _, testfunc in tests]
    testids = [
        f"{mod.__name__}::{testfunc.__name__}"
        for mod, testfunc in tests
    ]
    metafunc.parametrize(argnames=["testfunc"], argvalues=argvalues, ids=testids)


@pytest.mark.usefixtures("curses_setup")
def test_feature(mock_screen, testfunc):
    visidata.vd.resetVisiData()
    visidata.vd.scr = mock_screen
    testfunc(visidata.vd)
