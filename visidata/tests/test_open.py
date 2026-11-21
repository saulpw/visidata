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

    def test_filetype_does_not_bypass_download_scheme(self):
        'explicit -f filetype must reach the download loader, which fetches then honours it  #3278'
        origins = {name: getattr(vd, name) for name in ('open_csv', 'openurl_http', 'openurl_https', 'openurl_s3')}
        calls = []

        def fake_open_csv(p):
            calls.append(('open_csv', str(p)))
            return ('open_csv', str(p))

        def make_fake_openurl(scheme):
            def _fake(p, filetype=None):
                calls.append((f'openurl_{scheme}', filetype))
                return (f'openurl_{scheme}', str(p))
            return _fake

        vd.open_csv = fake_open_csv
        for scheme in ('http', 'https', 's3'):
            setattr(vd, f'openurl_{scheme}', make_fake_openurl(scheme))

        try:
            for scheme in ('http', 'https', 's3'):
                calls.clear()
                result = vd.openPath(Path(f'{scheme}://example.com/data.csv'), filetype='csv')
                # the url is fetched by the scheme loader, which then picks open_csv itself
                assert result[0] == f'openurl_{scheme}', calls
                assert calls == [(f'openurl_{scheme}', 'csv')], calls
        finally:
            for name, func in origins.items():
                setattr(vd, name, func)
