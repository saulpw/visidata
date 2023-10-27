
from visidata import vd, TableSheet
import pytest


class TestMenu:
    def test_menuitems(self):
        vd.addMenuItems('''Column > Add column > foobar > hello-world''')

        m = TableSheet().getMenuItem(['Column', 'Add column', 'foobar'])
        assert m

        with pytest.raises(AssertionError):
            vd.addMenuItems('''Column > Add column > non-command''')
