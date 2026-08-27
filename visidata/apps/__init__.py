'Loader stubs so `vd -f vdsql` etc. work without the app pre-loaded; the import replaces the stub.'

from visidata import vd, VisiData


@VisiData.api
def open_vdsql(vd, p, filetype=None):
    import visidata.apps.vdsql
    return vd.open_vdsql(p)


@VisiData.api
def open_git(vd, p):
    import visidata.apps.vgit
    return vd.open_git(p)
