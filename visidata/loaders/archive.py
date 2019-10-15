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

    def iterload(self):
        with zipfile.ZipFile(str(self.source), 'r') as zf:
            for zi in Progress(zf.infolist()):
                yield zi


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

    def iterload(self):
        with tarfile.open(name=str(self.source)) as tf:
            for ti in Progress(tf.getmembers()):
                yield ti


vd.filetype('zip', ZipSheet)
vd.filetype('tar', TarSheet)
vd.filetype('tgz', TarSheet)
vd.filetype('txz', TarSheet)
vd.filetype('tbz2', TarSheet)
