import pytest
import visidata

@pytest.mark.usefixtures('curses_setup')
class TestFeatures:
    def test_features(self, mock_screen):
        tests = [
            (mod, getattr(mod, k))
                for mod in visidata.vd.importedModules
                    for k in dir(mod)
                        if k.startswith('test_')
        ]
        for mod, testfunc in tests:
            print(mod, testfunc.__name__)
            visidata.vd.resetVisiData()
            visidata.vd.scr = mock_screen
            testfunc(visidata.vd)
