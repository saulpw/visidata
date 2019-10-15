import codecs
import tarfile
import zipfile

from visidata import *


class ZipSheet(Sheet):
    'Wrapper for `zipfile` library.'
    rowtype = 'files' # rowdef ZipInfo
    columns = [
        ColumnAttr('filename'),
        ColumnAttr('file_size', type=int),
        Column('date_time', type=date,
               getter=lambda col, row: datetime.datetime(*row.date_time)),
        ColumnAttr('compress_size', type=int)
    ]

    def openRow(self, fi):
            zfp = zipfile.ZipFile(str(self.source), 'r')
            decodedfp = codecs.iterdecode(zfp.open(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return openSource(Path(fi.filename, fp=decodedfp, filesize=fi.file_size))


    @asyncthread
    def reload(self):
        contents = zipfile.ZipFile(str(self.source), 'r').infolist()

        self.rows = []
        for row in Progress(contents):
            self.addRow(row)


class TarSheet(Sheet):
    'Wrapper for `tarfile` library.'
    rowtype = 'files' # rowdef TarInfo
    columns = [
        ColumnAttr('name'),
        ColumnAttr('size', type=int),
        ColumnAttr('mtime', type=date),
        ColumnAttr('type', type=int),
        ColumnAttr('mode', type=int),
        ColumnAttr('uname'),
        ColumnAttr('gname')
    ]

    def openRow(self, fi):
            tfp = tarfile.open(name=str(self.source))
            decodedfp = codecs.iterdecode(tfp.extractfile(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return openSource(Path(fi.name, fp=decodedfp, filesize=fi.size))

    @asyncthread
    def reload(self):
        contents = tarfile.open(name=str(self.source)).getmembers()

        self.rows = []
        for row in Progress(contents):
            self.addRow(row)


ZipSheet.addCommand(ENTER, 'dive-row', 'vd.push(openRow(cursorRow))')
ZipSheet.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(openRow(r))')
TarSheet.addCommand(ENTER, 'dive-row', 'vd.push(openRow(cursorRow))')
TarSheet.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(openRow(r))')

def open_zip(p):
    return ZipSheet(p.name, source=p)


def open_tar(p):
    return TarSheet(p.name, source=p)

open_tgz = open_tar
open_txz = open_tar
open_tbz2 = open_tar
