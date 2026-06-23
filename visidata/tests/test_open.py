from visidata import Path, vd


class TestOpenPath:
    def test_filetype_overrides_url_scheme(self):
        'explicit -f filetype with a dedicated open_<filetype> wins over url-scheme dispatch  #3126'
        vd.open_myfiletype = lambda p: ('open_myfiletype', str(p))
        vd.openurl_myscheme = lambda p, **kwargs: ('openurl_myscheme', str(p))

        p = Path('myscheme://host/db')

        # with explicit filetype, the open_<filetype> loader is used
        assert vd.openPath(p, filetype='myfiletype')[0] == 'open_myfiletype'

        # without a filetype, dispatch falls back to the url scheme
        assert vd.openPath(p)[0] == 'openurl_myscheme'
