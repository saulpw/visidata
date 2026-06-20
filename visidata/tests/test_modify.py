import pytest

import visidata
from visidata import vd, Path
from visidata.errors import ExpectedException


@pytest.mark.usefixtures('curses_setup')
class TestOverwrite:
    @pytest.mark.parametrize('val,expected', [
        ('c', True), ('confirm', True),
        ('y', True), ('yes', True),  # legacy overwrite=y  #3014
        ('n', False), ('never', False), ('', False),  #1805
    ])
    def test_couldOverwrite(self, val, expected):
        visidata.options.overwrite = val
        assert vd.couldOverwrite() == expected
        visidata.options.overwrite = 'c'

    def test_confirmOverwrite(self, tmp_path):
        fn = tmp_path/'exists.txt'
        fn.write_text('x')
        p = Path(str(fn))

        visidata.options.overwrite = 'y'  # legacy: overwrite without confirm
        assert vd.confirmOverwrite(p)

        for val in ('n', ''):
            visidata.options.overwrite = val
            with pytest.raises(ExpectedException):
                vd.confirmOverwrite(p)

        visidata.options.overwrite = 'c'  # confirm=y accepts the prompt
        assert vd.confirmOverwrite(p)
