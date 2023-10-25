
from visidata import vd, TableSheet


class TestMenu:
    def test_menuitems(self):
        vd.addMenuItems('''Column > Add column > foobar > hello-world''')

        m = TableSheet().getMenuItem(['Column', 'Add column', 'foobar'])
        assert m

        vd.addMenuItems('''Column > Add column > non-command''')
        m = TableSheet().getMenuItem(['Column', 'Add column'])
        assert m
