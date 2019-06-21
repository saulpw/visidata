import codecs
from visidata import *

class open_tar(Sheet):
    'Provide wrapper around `tarfile` library for opening TAR files.'
    rowtype = 'files'
    columns = [
        ColumnAttr('name'),
        ColumnAttr('size', type=int),
        ColumnAttr('mtime', type=date),
        ColumnAttr('type', type=int),
        ColumnAttr('mode', type=int),
        ColumnAttr('uname'),
        ColumnAttr('gname')
    ]

    def __init__(self, p):
        super().__init__(p.name, source=p)

    def reload(self):
        import tarfile
        with tarfile.open(name=self.source.resolve()) as tfp:
            self.rows = tfp.getmembers()

    def openTarFileEntry(self, ti):
        import tarfile
        tfp = tarfile.open(name=self.source.resolve())
        decodedfp = codecs.iterdecode(tfp.extractfile(ti), encoding=options.encoding, errors=options.encoding_errors)
        return openSource(PathFd(ti.name, decodedfp, filesize=ti.size))


open_tar.addCommand(ENTER, 'dive-row', 'vd.push(openTarFileEntry(cursorRow))')
open_tar.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(openTarFileEntry(r))')

open_tgz = open_tar
open_txz = open_tar
open_tbz2 = open_tar
