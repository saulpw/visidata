import codecs
import tarfile
import zipfile

from visidata import *

def open_zip(p):
    return ZipSheet(p.name, source=p)

def open_tar(p):
    return TarSheet(p.name, source=p)

open_tgz = open_tar
open_txz = open_tar
open_tbz2 = open_tar

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

    def openZipFile(self, fp, *args, **kwargs):
        '''Use VisiData input to handle password-protected zip files.'''
        try:
            return fp.open(*args, **kwargs)
        except RuntimeError as err:
            if 'password required' in err.args[0]:
                pwd = vd.input(f'{args[0].filename} is encrypted, enter password: ', display=False)
                return fp.open(*args, **kwargs, pwd=pwd.encode('utf-8'))
            vd.error(err)

    def openRow(self, fi):
            decodedfp = codecs.iterdecode(self.openZipFile(self.zfp, fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return vd.openSource(Path(fi.filename, fp=decodedfp, filesize=fi.file_size), filetype=options.filetype)

    @asyncthread
    def extract(self, *rows, path=None):
        self.zfp.extractall(members=[r.filename for r in rows], path=path)

    @property
    def zfp(self):
        return zipfile.ZipFile(str(self.source), 'r')

    def iterload(self):
        with self.zfp as zf:
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
            return vd.openSource(Path(fi.name, fp=decodedfp, filesize=fi.size))

    def iterload(self):
        with tarfile.open(name=str(self.source)) as tf:
            for ti in Progress(tf.getmembers()):
                yield ti


ZipSheet.addCommand('x', 'extract-file', 'extract(cursorRow)')
ZipSheet.addCommand('gx', 'extract-selected', 'extract(*onlySelectedRows)')
ZipSheet.addCommand('zx', 'extract-file-to', 'extract(cursorRow, path=inputPath("extract to: "))')
ZipSheet.addCommand('gzx', 'extract-selected-to', 'extract(*onlySelectedRows, path=inputPath("extract %d files to: " % nSelected))')
